"""
AI Assistant with weather and points of interest.
Orchestration only: uses injected LLM and tool registry.
"""

import json
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Protocol

from prompts import EXECUTE_REQUEST, PLAN_REQUEST, SYSTEM_PROMPT

# --- History helpers ---


def _msg_get(obj, key: str, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def ensure_system_message(history: list) -> list:
    """Ensure the conversation history starts with the system prompt."""
    if history and history[0].get("role") == "system":
        return list(history)
    return [{"role": "system", "content": SYSTEM_PROMPT}] + list(history)


def trim_history(messages: list) -> list:
    """
    Trim persisted history: keep system + real user/assistant turns;
    drop PLAN_REQUEST/EXECUTE_REQUEST scaffolding, plan message, tool call/result messages.
    """
    trimmed: list[dict] = []
    saw_system = False
    skip_next_assistant_plan = False

    for m in messages:
        role = _msg_get(m, "role", "")
        content = _msg_get(m, "content", "") or ""

        if role == "system":
            if not saw_system:
                trimmed.append({"role": "system", "content": content})
                saw_system = True
            continue

        if role == "tool":
            continue

        if role == "user" and content in (PLAN_REQUEST, EXECUTE_REQUEST):
            if content == PLAN_REQUEST:
                skip_next_assistant_plan = True
            continue

        if role == "assistant":
            tool_calls = _msg_get(m, "tool_calls", None)
            if tool_calls:
                continue
            if skip_next_assistant_plan:
                skip_next_assistant_plan = False
                continue
            trimmed.append({"role": "assistant", "content": content})
            continue

        if role == "user":
            skip_next_assistant_plan = False
            trimmed.append({"role": "user", "content": content})
            continue

    if not saw_system:
        return [{"role": "system", "content": SYSTEM_PROMPT}] + trimmed
    return trimmed

# --- Plan heuristic ---


def _is_weather_query(text: str) -> bool:
    t = (text or "").lower()
    return any(
        k in t
        for k in (
            "weather",
            "forecast",
            "temperature",
            "temp",
            "rain",
            "wind",
            "humidity",
            "humid",
            "cloud",
            "sun",
            "snow",
        )
    )


def _wants_places_or_itinerary(text: str) -> bool:
    t = (text or "").lower()
    return any(
        k in t
        for k in (
            "itinerary",
            "plan a trip",
            "trip",
            "things to do",
            "what to do",
            "recommend",
            "suggest",
            "where to eat",
            "restaurant",
            "restaurants",
            "museum",
            "museums",
            "park",
            "parks",
            "places",
            "poi",
        )
    )


def should_use_plan(user_message: str) -> bool:
    """Heuristic to skip the plan call for simple queries (latency reduction)."""
    t = (user_message or "").strip()
    if not t:
        return False
    if _wants_places_or_itinerary(t):
        return True
    words = t.split()
    if _is_weather_query(t) and len(words) <= 10:
        return False
    if len(words) <= 6:
        return False
    return True

# --- LLM protocol and OpenAI client ---


class StreamChunk:
    """One chunk from a streamed completion."""

    __slots__ = ("content", "tool_calls", "finish_reason")

    def __init__(
        self,
        *,
        content: str | None = None,
        tool_calls: list[dict[str, Any]] | None = None,
        finish_reason: str | None = None,
    ) -> None:
        self.content = content
        self.tool_calls = tool_calls or []
        self.finish_reason = finish_reason


class LLMClient(Protocol):
    """Protocol for an LLM that supports streamed chat completion with tools."""

    def stream_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        tool_choice: str,
    ) -> Iterator[StreamChunk]:
        ...


class OpenAILLMClient:
    """Wraps OpenAI client and implements stream_completion for the assistant."""

    def __init__(self, client: Any, model: str = "gpt-4o-mini") -> None:
        self._client = client
        self._model = model

    def stream_completion(
        self,
        messages: list[dict],
        tools: list[dict],
        tool_choice: str,
    ):
        stream = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            stream=True,
        )
        for chunk in stream:
            choice = chunk.choices[0]
            delta = choice.delta
            content = getattr(delta, "content", None)
            finish_reason = choice.finish_reason if choice.finish_reason else None
            tool_calls_out: list[dict] = []
            delta_tool_calls = getattr(delta, "tool_calls", None)
            if delta_tool_calls:
                for tc in delta_tool_calls:
                    entry: dict = {
                        "index": tc.index,
                        "id": getattr(tc, "id", None) or "",
                        "type": "function",
                        "function": {"name": "", "arguments": ""},
                    }
                    fn = getattr(tc, "function", None)
                    if fn:
                        if getattr(fn, "name", None):
                            entry["function"]["name"] = fn.name
                        if getattr(fn, "arguments", None):
                            entry["function"]["arguments"] += fn.arguments
                    tool_calls_out.append(entry)
            yield StreamChunk(
                content=content,
                tool_calls=tool_calls_out,
                finish_reason=finish_reason,
            )


# --- Run assistant ---


def run_assistant(
    conversation_history: list,
    user_message: str,
    llm: LLMClient,
    tool_registry: Any,
    user_preferences: str | None = None,
):
    """
    Process user message with the assistant (plan-and-execute).
    Yields ("plan", plan_text), ("plan_delta", chunk), ("delta", text), ("result", ...).
    If user_preferences is non-empty, it is injected into the system message for personalized trip planning.
    """
    messages = ensure_system_message(conversation_history)
    if user_preferences and user_preferences.strip():
        pref_block = "\n\nUser's travel preferences (use these to personalize recommendations and itineraries):\n" + user_preferences.strip()
        if messages and messages[0].get("role") == "system":
            messages[0] = {"role": "system", "content": messages[0]["content"] + pref_block}
    messages.append({"role": "user", "content": user_message})

    tools = tool_registry.get_schemas()

    if should_use_plan(user_message):
        messages.append({"role": "user", "content": PLAN_REQUEST})
        plan_parts: list[str] = []
        for chunk in llm.stream_completion(messages, tools, "none"):
            if chunk.content:
                plan_parts.append(chunk.content)
                yield ("plan_delta", chunk.content)
        plan_text = "".join(plan_parts)
        messages.append({"role": "assistant", "content": plan_text or ""})
        messages.append({"role": "user", "content": EXECUTE_REQUEST})
        yield ("plan", (plan_text or "").strip() or None)

    weather_api_used = False
    places_api_used = False

    while True:
        content_parts: list[str] = []
        tool_calls_by_index: dict[int, dict] = {}
        saw_tool_calls = False
        finish_reason = None

        for chunk in llm.stream_completion(messages, tools, "auto"):
            if chunk.finish_reason:
                finish_reason = chunk.finish_reason
            for tc in chunk.tool_calls:
                saw_tool_calls = True
                idx = tc.get("index", 0)
                entry = tool_calls_by_index.setdefault(
                    idx,
                    {"id": "", "type": "function", "function": {"name": "", "arguments": ""}},
                )
                if tc.get("id"):
                    entry["id"] = tc["id"]
                fn = tc.get("function", {})
                if fn.get("name"):
                    entry["function"]["name"] = fn["name"]
                if fn.get("arguments"):
                    entry["function"]["arguments"] += fn["arguments"]
            if chunk.content:
                content_parts.append(chunk.content)
                if not saw_tool_calls:
                    yield ("delta", chunk.content)

        content = "".join(content_parts)
        tool_calls = [tool_calls_by_index[i] for i in sorted(tool_calls_by_index.keys())]

        if finish_reason == "stop":
            messages.append({"role": "assistant", "content": content or ""})
            trimmed = trim_history(messages)
            yield (
                "result",
                content or "",
                weather_api_used,
                places_api_used,
                trimmed,
            )
            return

        if finish_reason == "tool_calls" and tool_calls:
            messages.append({"role": "assistant", "content": content or "", "tool_calls": tool_calls})
            results_by_id: dict[str, tuple[str, bool, bool]] = {}

            def process_one_tool_call(tc):
                if isinstance(tc, dict):
                    name = tc.get("function", {}).get("name", "")
                    args_raw = tc.get("function", {}).get("arguments", "") or "{}"
                    tool_call_id = tc.get("id", "")
                else:
                    name = tc.function.name
                    args_raw = tc.function.arguments or "{}"
                    tool_call_id = tc.id

                args = json.loads(args_raw)
                result = tool_registry.run(name, args)
                is_weather = name in ("get_current_temperature", "get_weather_forecast")
                is_places = name == "search_places"
                return tool_call_id, result, is_weather, is_places

            with ThreadPoolExecutor(max_workers=min(32, len(tool_calls) * 2)) as executor:
                futures = [executor.submit(process_one_tool_call, tc) for tc in tool_calls]
                for future in as_completed(futures):
                    tool_call_id, result, is_weather, is_places = future.result()
                    results_by_id[tool_call_id] = (result, is_weather, is_places)
                    if is_weather:
                        weather_api_used = True
                    if is_places:
                        places_api_used = True

            for tc in tool_calls:
                tc_id = tc["id"] if isinstance(tc, dict) else tc.id
                tool_content, _, _ = results_by_id[tc_id]
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc_id,
                        "content": tool_content,
                    }
                )
            continue

        messages.append({"role": "assistant", "content": content or ""})
        trimmed = trim_history(messages)
        yield (
            "result",
            content or "",
            weather_api_used,
            places_api_used,
            trimmed,
        )
        return
