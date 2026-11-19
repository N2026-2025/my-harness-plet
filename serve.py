# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Plan-verify harness with MCP tool support and streaming.

Combines three-role architecture (planner/worker/verifier) with MCP tools,
streaming responses, context compaction, and robust error recovery.
"""

from __future__ import annotations

import asyncio
import json
import os
import posixpath
import re
import sys
import types
from typing import Any

import openai
import taskbridge

MODEL = os.environ.get("MODEL_NAME", "")
MAX_EFFORT_MODELS = ("claude", "glm", "gpt-6", "deepseek-v4")
EFFORT = os.environ.get("REASONING_EFFORT") or (
    "max" if any(m in MODEL.lower() for m in MAX_EFFORT_MODELS) else "high"
)
RESPONSES_MODELS = ("gpt-6",)
RESPONSES_ONLY = re.compile(
    r"/v1/responses|not supported.{0,80} in /v1/chat/completions"
)
CACHE_MARK = "claude" in MODEL.lower()
COMPACT_AT_TOKENS = int(os.environ.get("COMPACT_AT_TOKENS", "150000"))
TOOL_RESULT_CHARS = 30_000
DIRECT_MCP_CHARS = 40_000
MAX_TOOLS = 128
KEEP_RECENT_RESULTS = 12
FINISH_MARGIN_SEC = 180
RETRY_WAITS = (5, 15, 30, 60, 120)
CONTEXT_FULL = re.compile(
    r"context.?(length|window|size|limit)|maximum context|too many"
    r" tokens|prompt is too long|maximum prompt length"
    r"|(input|prompt|request|messages?)\b[^.]{0,40}(too long|exceed)"
    r"|exceed[^.]{0,40}(token|context)",
    re.I,
)
WINDOW_RE = re.compile(
    r"maximum context length (?:is |of )?(\d+)"
    r"|context (?:window|length|size)(?: limit)?(?: is| of)? (\d+)"
    r"|tokens? > (\d+) maximum|maximum number of tokens allowed \((\d+)\)"
    r"|maximum prompt length is (\d+)",
    re.I,
)
PROMPT_RE = re.compile(
    r"(\d+) input tokens|(\d+) in the messages|prompt is too long: (\d+)"
    r"|input token count \((\d+)\)|request contains (\d+) tokens",
    re.I,
)
MIN_OUTPUT = 1024
UNREAD_KEEP = 600
CONTEXT_MARGIN = 1024
UNSUPPORTED = re.compile(
    r"unsupported|unrecogni[sz]ed|unknown|not supported|does not support|not"
    r" (allowed|permitted)"
    r"|extra (inputs|fields)|unexpected",
    re.I,
)
CALL_FIELDS = {"index", "id", "type", "function"}
FUNCTION_FIELDS = {"name", "arguments"}
DELTA_FIELDS = {
    "role",
    "content",
    "tool_calls",
    "function_call",
    "refusal",
    "audio",
    "annotations",
    "reasoning_content",
    "reasoning",
}

client = openai.AsyncOpenAI(
    base_url=os.environ.get("MODEL_BASE_URL"),
    api_key=os.environ.get("MODEL_API_KEY") or "none",
    max_retries=0,
    timeout=900,
)

PLANNER = """You plan an engineering task that another engineer will carry out in a Linux container with no internet \
access. Inspect the task's files with your tools (bash starts in {workdir}), but do not create or change any file. \
Then reply with the plan: each deliverable with its exact path and format, what it must contain, the data and method \
to use, and how to check it.{mcp}"""

WORKER = """You are an expert engineer working on a task in a Linux container with no internet access. Your tools \
act inside it, and bash starts in {workdir}. A plan for the task follows it; use it, and correct it where the files \
show it is wrong. Compute with code, not by hand. Write each deliverable exactly where and in the format the task \
asks, then open it again to check it. When you are done, reply without calling a tool: a short summary of each \
deliverable, where it is, and the key results.{mcp}"""

VERIFIER = """You check an engineer's work on a task in a Linux container. You get the task, the plan, and the \
engineer's summary of what was delivered. Open every deliverable with your tools (bash starts in {workdir}) and check \
it against the task: the path, the format, every part the task asks for, and the key numbers, recomputed. Do not \
create or change any file. If everything holds, reply with the single word PASS and nothing else. Otherwise reply \
with a numbered list of the gaps, each specific enough to fix.{mcp}"""

MCP_DIRECT = """

The task also offers its own tools (the functions named <server>__<tool>)."""

MCP_CATALOG = """

The task also offers its own tools, listed below by server. Call mcp_find to see a tool's parameters, then mcp_call \
to run it.
{catalog}"""

SUMMARY_PROMPT = """The conversation is getting long, so the earlier turns will be removed. Write notes that let you \
continue without them: what the task requires, what you found in the files, every file you created or changed (with \
its path and state), the numbers and decisions so far, and what remains to do. Be specific."""

WRAP_UP = {
    "role": "user",
    "content": "Time is up for this step. Stop and reply with your answer.",
}
WRAP_UP_SEC = 240
MAX_NUDGES = 3
MAX_OUTPUT_TOKENS = int(os.environ.get("MAX_OUTPUT_TOKENS", "32000"))
PLAN_SHARE = 0.1
CHECK_SHARE = 0.25
MIN_STEP_SEC = 120
MAX_FIX_ROUNDS = 2


def tool(
    name: str, description: str, required: list[str], **properties: Any
) -> dict[str, Any]:
    """Builds an OpenAI function-tool definition dictionary."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


TOOLS = [
    tool(
        "bash",
        "Run a bash command in the task container and return its exit code and"
        " output. Each call starts a new shell in the working directory: only"
        " files persist between calls.",
        ["command"],
        command={"type": "string"},
        timeout_sec={
            "type": "integer",
            "description": (
                "Stop the command after this many seconds (default 120)."
            ),
        },
    ),
    tool(
        "read_file",
        "Read a text file from the task container.",
        ["path"],
        path={"type": "string"},
    ),
    tool(
        "write_file",
        "Create or overwrite a file in the task container; parent directories"
        " are created.",
        ["path", "content"],
        path={"type": "string"},
        content={"type": "string"},
        append={
            "type": "boolean",
            "description": (
                "Add to the end of the file instead (write a large file in"
                " parts)."
            ),
        },
    ),
    tool(
        "edit_file",
        "Replace exact text in a file. old_text must occur exactly once unless"
        " replace_all is true.",
        ["path", "old_text", "new_text"],
        path={"type": "string"},
        old_text={"type": "string"},
        new_text={"type": "string"},
        replace_all={"type": "boolean"},
    ),
]
READ_ONLY = TOOLS[:2]
MCP_TOOLS = [
    tool(
        "mcp_find",
        "Show the description and parameters of the task's own tools that match"
        " a query.",
        ["query"],
        query={
            "type": "string",
            "description": "A tool name, or words describing what you need.",
        },
    ),
    tool(
        "mcp_call",
        "Run one of the task's own tools.",
        ["tool", "arguments"],
        tool={"type": "string", "description": "The tool's name as listed."},
        arguments={"type": "object"},
    ),
]


def clip(text: str, limit: int = TOOL_RESULT_CHARS) -> str:
    """Truncates `text` in the middle if it exceeds `limit` characters."""
    if len(text) <= limit:
        return text
    head = limit * 2 // 3
    return (
        f"{text[:head]}\n[... {len(text) - limit} characters cut"
        f" ...]\n{text[-(limit - head):]}"
    )


def parse_arguments(call: dict[str, Any]) -> dict[str, Any] | str:
    """Parses a tool call's arguments into a dict or returns an error string."""

    def reject(constant):
        raise ValueError(f"{constant} is not valid JSON")

    try:
        args = json.loads(call["arguments"] or "{}", parse_constant=reject)
        if not isinstance(args, dict):
            raise ValueError("the arguments must be a JSON object")
        call["arguments"] = (
            json.dumps(args, ensure_ascii=False)
            .encode("utf-8", "replace")
            .decode("utf-8")
        )
        return args
    except ValueError as exc:
        call["arguments"] = "{}"
        return (
            f"error: the arguments are not a valid JSON object ({exc}); send the"
            " call again"
        )


def unique_name(name: str, taken: Any) -> str:
    """Truncates `name` to 64 chars and appends `_2`, `_3`, ... if in `taken`."""
    candidate, n = name[:64], 1
    while candidate in taken:
        n += 1
        candidate = f"{name[:63 - len(str(n))]}_{n}"
    return candidate


def visible(text: str) -> str:
    """Strips `<?>...<?>` reasoning blocks from `text`."""
    return re.sub(r"<\?.*?(\?>|$)", "", text or "", flags=re.S).strip()


def extra_fields(part: Any, known: set[str]) -> dict[str, Any]:
    """Extracts non-null extra fields from a streamed SDK object `part`."""
    fields = getattr(part, "model_extra", None) or {}
    return {k: v for k, v in fields.items() if k not in known and v is not None}


def merged(old: Any, new: Any, key: str = "") -> Any:
    """Merges a single delta's extra field value `new` into `old`."""
    if key == "thinking_blocks" and isinstance(new, list):
        return thinking_blocks(old if isinstance(old, list) else [], new)
    if isinstance(old, dict) and isinstance(new, dict):
        return {**old, **{k: merged(old.get(k), v, k) for k, v in new.items()}}
    if isinstance(old, list) and isinstance(new, list):
        return old + new
    return new


def thinking_blocks(
    blocks: list[dict[str, Any]], new: list[Any]
) -> list[dict[str, Any]]:
    """Accumulates streamed Claude `thinking_blocks` deltas."""
    out = [dict(b) for b in blocks]
    for b in new:
        if not isinstance(b, dict):
            continue
        last = out[-1] if out else None
        if (
            last is None
            or last.get("signature")
            or last.get("data")
            or b.get("data")
            or last.get("type") != b.get("type")
        ):
            out.append(dict(b))
            continue
        last["thinking"] = (last.get("thinking") or "") + (b.get("thinking") or "")
        if b.get("signature"):
            last["signature"] = b["signature"]
    return out


def signed(block: Any) -> bool:
    """Returns whether `block` has a `signature` or redacted `data` field."""
    return isinstance(block, dict) and bool(
        block.get("signature") or block.get("data")
    )


def drop_thinking(
    message: dict[str, Any], unless: Any = lambda block: False
) -> dict[str, Any]:
    """Filters `thinking_blocks` in `message`, keeping blocks matching `unless`."""
    if isinstance(message.get("thinking_blocks"), list):
        message["thinking_blocks"] = [
            b for b in message["thinking_blocks"] if unless(b)
        ]
    fields = message.get("provider_specific_fields")
    if isinstance(fields, dict) and isinstance(
        fields.get("thinking_blocks"), list
    ):
        message["provider_specific_fields"] = {
            **fields,
            "thinking_blocks": [b for b in fields["thinking_blocks"] if unless(b)],
        }
    return message


def marked(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Returns the messages a Chat Completions call sends."""
    if not CACHE_MARK:
        return messages
    out = list(messages)
    for i in {0, len(out) - 1}:
        m, content = out[i], out[i].get("content")
        if isinstance(content, str) and content:
            out[i] = {
                **m,
                "content": [{
                    "type": "text",
                    "text": content,
                    "cache_control": {"type": "ephemeral"},
                }],
            }
        else:
            out[i] = {**m, "cache_control": {"type": "ephemeral"}}
    return out


def response_input(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Converts Chat Completions messages into Responses API input items."""
    items = []
    for m in messages:
        if m["role"] == "tool":
            items.append({
                "type": "function_call_output",
                "call_id": m["tool_call_id"],
                "output": m["content"],
            })
        elif m["role"] != "assistant":
            items.append({"role": m["role"], "content": m["content"]})
        elif "output_items" in m:
            calls = iter(m.get("tool_calls") or [])
            for item in m["output_items"]:
                call = None
                if item.get("type") == "function_call":
                    call = next(calls, None)
                if call:
                    item = {
                        **item,
                        "call_id": call["id"],
                        "name": call["function"]["name"],
                        "arguments": call["function"]["arguments"],
                    }
                items.append(item)
        else:
            if m.get("content"):
                items.append({"role": "assistant", "content": m["content"]})
            items += [
                {
                    "type": "function_call",
                    "call_id": c["id"],
                    "name": c["function"]["name"],
                    "arguments": c["function"]["arguments"],
                }
                for c in m.get("tool_calls") or []
            ]
    return items


def chat_usage(usage: Any) -> Any:
    """Returns Responses API `usage` in the shape `record` and `report` read."""
    if usage is None:
        return None
    details = getattr(usage, "input_tokens_details", None)
    return types.SimpleNamespace(
        prompt_tokens=usage.input_tokens or 0,
        completion_tokens=usage.output_tokens or 0,
        prompt_tokens_details=types.SimpleNamespace(
            cached_tokens=getattr(details, "cached_tokens", 0) or 0
        ),
    )


class MCPServer(taskbridge.MCPClient):
    """Client wrapper for a single task MCP server and its discovered tools."""

    def __init__(self, session: taskbridge.Session, spec: dict[str, Any]):
        super().__init__(session, spec["url"], client="custom-harness")
        self.name = spec["name"]
        self.tools: list[dict[str, Any]] = []

    async def start(self) -> None:
        """Initializes the MCP session and fetches the server's tool list."""
        await self.initialize()
        self.tools = await self.list_tools()

    async def call(self, name: str, arguments: dict[str, Any]) -> str:
        """Calls tool `name` on the MCP server and formats the result as text."""
        result = await self.call_tool(name, arguments)
        parts = []
        content = (
            result.get("content") if isinstance(result.get("content"), list) else []
        )
        for item in content:
            kind = item.get("type") if isinstance(item, dict) else None
            if kind == "text":
                parts.append(str(item.get("text", "")))
            elif kind == "resource":
                parts.append(json.dumps(item.get("resource"))[:TOOL_RESULT_CHARS])
            elif kind == "resource_link":
                parts.append(json.dumps(item)[:TOOL_RESULT_CHARS])
            else:
                parts.append(f"[{kind or 'unknown'} content not shown]")
        if not parts and result.get("structuredContent") is not None:
            parts.append(json.dumps(result["structuredContent"]))
        text = "\n".join(parts) or "(no content)"
        return f"error: {text}" if result.get("isError") else text


class Reply:
    """Accumulates a streamed chat-completion response and its tool calls."""

    def __init__(self):
        self.text, self.reasoning, self.calls, self.usage, self.finish = (
            "",
            "",
            {},
            None,
            None,
        )
        self.extra = {}
        self._by_index, self._by_id, self._last = {}, {}, None

    def add_call(self, part: Any) -> None:
        """Adds one streamed tool-call delta to the accumulated calls."""
        index, call_id = (
            getattr(part, "index", None),
            getattr(part, "id", None) or "",
        )
        function = getattr(part, "function", None)
        name = (getattr(function, "name", None) or "") if function else ""
        key = self._by_index.get(index) if index is not None else None
        if (
            key is not None
            and call_id
            and self.calls[key]["id"] not in ("", call_id)
        ):
            key = None
        if (
            key is not None
            and not call_id
            and name
            and self._another_call(self.calls[key], name)
        ):
            key = None
        if key is None and call_id:
            key = self._by_id.get(call_id)
        if (
            key is None
            and index is None
            and not call_id
            and self._last is not None
            and not (name and self._another_call(self.calls[self._last], name))
        ):
            key = self._last
        if key is None:
            key = len(self.calls)
            self.calls[key] = {
                "id": "",
                "name": "",
                "arguments": "",
                "extra": {},
                "function_extra": {},
            }
        if index is not None:
            self._by_index[index] = key
        if call_id:
            self._by_id[call_id] = key
        call = self.calls[key]
        call["id"] = call["id"] or call_id
        call["name"] = call["name"] or name
        call["arguments"] += (
            (getattr(function, "arguments", None) or "") if function else ""
        )
        call["extra"] = merged(call["extra"], extra_fields(part, CALL_FIELDS))
        if function:
            call["function_extra"] = merged(
                call["function_extra"], extra_fields(function, FUNCTION_FIELDS)
            )
        self._last = key

    @staticmethod
    def _another_call(call: dict[str, Any], name: str) -> bool:
        """Checks whether a nameless-ID delta for `name` starts a new tool call."""
        if not call["name"]:
            return False
        if name != call["name"]:
            return True
        try:
            return isinstance(json.loads(call["arguments"]), dict)
        except ValueError:
            return False

    def message(self) -> dict[str, Any]:
        """Builds the assistant message dict for the conversation history."""
        message = {**self.extra, "role": "assistant", "content": self.text or None}
        if self.calls:
            message["tool_calls"] = [
                {
                    **c["extra"],
                    "id": c["id"],
                    "type": "function",
                    "function": {
                        **c["function_extra"],
                        "name": c["name"],
                        "arguments": c["arguments"],
                    },
                }
                for c in self.calls.values()
            ]
        if self.reasoning:
            message["reasoning_content"] = self.reasoning
        return drop_thinking(message, unless=signed)


class OutOfTime(Exception):
    """Raised when retrying a failed model call would exceed the time budget."""


class CutOff(asyncio.TimeoutError):
    """Raised when a streamed reply is cut off by its per-call deadline."""


class StreamBadRequest(openai.OpenAIError):
    """Raised when an SSE stream reports a non-retryable bad request error."""


BAD_REQUEST = frozenset({
    "invalid_request_error",
    "context_length_exceeded",
    "invalid_value",
    "invalid_prompt",
})


def stream_error(error: Any) -> openai.OpenAIError:
    """Classifies an in-stream error object as a bad request or a truncated stream."""
    def field(name: str) -> Any:
        if isinstance(error, dict):
            return error.get(name)
        return getattr(error, name, None)

    message = str(field("message") or "")
    named = {field("type"), field("code")} & BAD_REQUEST
    if named or CONTEXT_FULL.search(message):
        return StreamBadRequest(message)
    return StreamCut(f"the stream reported an error: {message}")


class StreamCut(openai.OpenAIError):
    """Raised when an SSE stream ends before reporting a finish reason."""


class Agent:
    """Manages the conversation, tool execution, and context compaction loop."""

    def __init__(self, session: taskbridge.Session, role: str = "worker"):
        self.session = session
        self.role = role
        self.tools = list(TOOLS)
        self.mcp: dict[str, tuple[MCPServer, dict[str, Any]]] = {}
        self.messages: list[dict[str, Any]] = []
        self.prompt_tokens = 0
        self.output_ceiling = int(os.environ.get("MAX_OUTPUT_TOKENS", "32000"))
        self.context_window: int | None = None
        self.max_output = self.output_ceiling
        self.token_limit = "max_completion_tokens"
        self.effort = {"reasoning_effort": EFFORT}
        self.responses = MODEL.lower().startswith(RESPONSES_MODELS)
        self.finish_margin = FINISH_MARGIN_SEC

    async def run(self) -> str:
        """Runs the agent tool-calling loop until the task is complete."""
        mcp = await self.connect_mcp()
        left = self.session.time_left()
        self.finish_margin = (
            FINISH_MARGIN_SEC
            if left is None
            else min(FINISH_MARGIN_SEC, max(left, 0) / 4)
        )
        system = self.get_system_prompt(mcp)
        self.messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": self.session.instruction},
        ]
        nudges, head = 0, ""
        while True:
            left = self.session.time_left()
            if left is not None and left < self.finish_margin:
                return await self.finish("Time is almost up.")
            try:
                reply = await self.complete(head=head)
            except OutOfTime:
                return await self.finish(
                    "Time is almost up, and the model is not answering."
                )
            except CutOff:
                return await self.finish("Time is almost up.")
            arguments = [parse_arguments(call) for call in reply.calls.values()]
            if reply.text or reply.calls:
                self.messages.append(reply.message())
            text = visible(head + reply.text)
            if text:
                self.session.final_message = text
            if not reply.calls:
                if visible(reply.text) and reply.finish == "length":
                    nudges, head = 0, head + reply.text
                    self.messages.append({
                        "role": "user",
                        "content": (
                            f"Your reply was cut off at the {self.max_output}-token"
                            " output limit. Continue where it stopped, and put long"
                            " content in files with write_file rather than in a reply."
                        ),
                    })
                    continue
                if visible(reply.text) or nudges >= 2:
                    return text or self.session.final_message
                nudges += 1
                self.messages.append({
                    "role": "user",
                    "content": (
                        "Continue the task; when it is done, answer with "
                        "your summary of the deliverables."
                    ),
                })
                continue
            nudges, head = 0, ""
            for call, args in zip(reply.calls.values(), arguments):
                result = (
                    await self.run_tool(call["name"], args)
                    if isinstance(args, dict)
                    else args
                )
                if reply.finish == "length" and isinstance(args, str):
                    result += (
                        f" Your reply hit the {self.max_output}-token output limit; write"
                        " large files in parts."
                    )
                self.messages.append(
                    {"role": "tool", "tool_call_id": call["id"], "content": result}
                )
            left = self.session.time_left()
            if left is not None:
                self.messages[-1]["content"] += f"\n[{int(left // 60)} minutes left]"
            if self.prompt_tokens > self.compact_at():
                await self.compact()

    def get_system_prompt(self, mcp: str) -> str:
        """Returns the system prompt for this agent's role."""
        workdir = self.session.workdir
        if self.role == "planner":
            return PLANNER.format(workdir=workdir, mcp=mcp)
        elif self.role == "verifier":
            return VERIFIER.format(workdir=workdir, mcp=mcp)
        else:
            return WORKER.format(workdir=workdir, mcp=mcp)

    def get_tools(self) -> list[dict[str, Any]]:
        """Returns the tool set for this agent's role."""
        if self.role in ("planner", "verifier"):
            return READ_ONLY
        return self.tools

    async def finish(self, why: str) -> str:
        """Prompts the model for a final summary without tools when time is up."""
        self.messages.append({
            "role": "user",
            "content": (
                f"{why} Stop working now and answer with your final "
                "summary: what you delivered, where, and the key results."
            ),
        })
        left = self.session.time_left()
        reserve = (
            0 if left is None else left - max(5, taskbridge.time_share(left, 30))
        )
        try:
            text = visible(
                (
                    await self.complete(tool_choice="none", reserve=reserve, head="")
                ).text
            )
        except (CutOff, openai.OpenAIError, OutOfTime):
            text = ""
        return text or self.session.final_message

    async def connect_mcp(self) -> str:
        """Connects to the task's MCP servers and registers their tools."""
        for spec in self.session.mcp_servers:
            server = MCPServer(self.session, spec)
            try:
                await server.start()
            except (taskbridge.TaskError, RuntimeError, ValueError) as exc:
                await self.session.log(f"MCP server {server.name} unavailable: {exc}")
                continue
            for t in server.tools:
                name = re.sub(r"[^A-Za-z0-9_-]", "_", f"{server.name}__{t['name']}")
                self.mcp[unique_name(name, self.mcp)] = (server, t)
            await self.session.log(
                f"MCP server {server.name}: {len(server.tools)} tools"
            )
        if not self.mcp:
            return ""
        functions = [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": (t.get("description") or t["name"])[:1024],
                    "parameters": (
                        {
                            k: v
                            for k, v in (t.get("inputSchema") or {}).items()
                            if k != "$schema"
                        }
                        or {"type": "object", "properties": {}}
                    ),
                },
            }
            for name, (_, t) in self.mcp.items()
        ]
        if (
            len(json.dumps(functions)) <= DIRECT_MCP_CHARS
            and len(self.tools) + len(functions) <= MAX_TOOLS
        ):
            self.tools += functions
            return MCP_DIRECT
        self.tools += MCP_TOOLS
        servers: dict[str, list[str]] = {}
        for name, (server, _) in self.mcp.items():
            servers.setdefault(server.name, []).append(name)
        return MCP_CATALOG.format(
            catalog="\n".join(
                f"{s}: {', '.join(names)}" for s, names in servers.items()
            )
        )

    def find_mcp(self, query: str) -> str:
        """Finds MCP tools matching `query` and formats their schemas."""
        words = [w for w in re.split(r"[^a-z0-9]+", query.lower()) if w]

        def score(item):
            name, (_, t) = item
            text = f"{name} {t.get('description') or ''}".lower()
            return (
                (query == name) * 100
                + sum(w in name.lower() for w in words) * 3
                + sum(w in text for w in words)
            )

        best = [
            item
            for item in sorted(self.mcp.items(), key=score, reverse=True)[:8]
            if score(item) > 0
        ]
        if not best:
            return (
                f"no tool matches {query!r}; the names are listed in the system"
                " prompt"
            )
        found = [
            f"{name}: {(t.get('description') or '')[:400]}\nparameters:"
            f" {json.dumps(t.get('inputSchema') or {})}"
            for name, (_, t) in best
        ]
        while len(found) > 1 and len("\n\n".join(found)) > TOOL_RESULT_CHARS:
            found.pop()
        return "\n\n".join(found)

    async def complete(
        self,
        tool_choice: str = "auto",
        reserve: float | None = None,
        head: str | None = None,
    ) -> Reply:
        """Streams one model completion with retries and context-limit recovery."""
        reserve = self.finish_margin if reserve is None else reserve
        waits = iter(RETRY_WAITS)
        while True:
            try:
                reply = await self.stream(self.messages, tool_choice, reserve, head)
                if reply.finish is None:
                    raise StreamCut("the stream ended without a finish reason")
                await self.record(reply)
                return reply
            except openai.APIStatusError as exc:
                if exc.status_code == 400 and await self.remedy(str(exc)):
                    continue
                if not (exc.status_code in (408, 409, 429) or exc.status_code >= 500):
                    raise
                failure = exc
            except StreamBadRequest as exc:
                if await self.remedy(str(exc)):
                    continue
                raise
            except (openai.APIError, StreamCut) as exc:
                failure = exc
            wait = next(waits, None)
            if wait is None:
                raise failure
            left = self.session.time_left()
            if left is not None and left - wait < reserve:
                await self.session.log(
                    f"model call failed ({str(failure)[:300]}); no time left to wait"
                    f" {wait}s"
                )
                raise OutOfTime(str(failure)[:300]) from failure
            await self.session.log(
                f"model call failed ({str(failure)[:300]}); again in {wait}s"
            )
            await asyncio.sleep(wait)

    async def remedy(self, error: str) -> bool:
        """Adjusts request parameters for the next call after a bad request."""
        if CONTEXT_FULL.search(error):
            sent, measured = self.max_output, self.learn_context(error)
            if (
                measured
                and self.room() >= MIN_OUTPUT
                and self.output_limit() < sent
            ):
                return True
            return bool(
                await self.compact(force=True)
                or (not measured and self.output_limit() < sent)
                or self.cut_unread()
            )
        return (
            self.use_responses(error)
            or self.use_max_tokens(error)
            or self.drop_effort(error)
            or self.shrink_output(error)
        )

    def use_responses(self, error: str) -> bool:
        """Switches to the Responses API if a Chat Completions 400 points there."""
        if self.responses or not RESPONSES_ONLY.search(error):
            return False
        self.responses = True
        return True

    def use_max_tokens(self, error: str) -> bool:
        """Switches to `max_tokens` if `error` rejects `max_completion_tokens`."""
        if (
            self.token_limit != "max_completion_tokens"
            or "max_completion_tokens" not in error
            or not UNSUPPORTED.search(error)
        ):
            return False
        self.token_limit = "max_tokens"
        return True

    def drop_effort(self, error: str) -> bool:
        """Stops sending `reasoning_effort` once an endpoint refuses it."""
        if not self.effort or not re.search(r"reasoning[._]effort", error):
            return False
        self.effort = {}
        return True

    def shrink_output(self, error: str) -> bool:
        """Lowers `output_ceiling` when `error` indicates a smaller output limit."""
        if UNSUPPORTED.search(error):
            return False
        limit = re.search(r"(\d+)\s*\(exclusive\)", error)
        stated = re.search(
            r"at most (\d+)|(\d+), which is the maximum|maximum (?:allowed"
            r" )?(?:number of )?(?:output|"
            r"completion) tokens (?:is |of )?(\d+)",
            error,
            re.I,
        )
        if limit:
            new = int(limit.group(1)) - 1
        elif stated:
            new = int(next(g for g in stated.groups() if g))
        elif re.search(
            r"max_?(completion_)?tokens|maxOutputTokens|output tokens", error, re.I
        ):
            new = self.max_output // 2
        else:
            return False
        if new >= self.max_output or new < MIN_OUTPUT:
            return False
        self.output_ceiling = new
        return True

    def learn_context(self, error: str) -> bool:
        """Extracts context window and prompt token counts from `error`."""
        window, prompt = WINDOW_RE.search(error), PROMPT_RE.search(error)
        if window:
            self.context_window = int(next(g for g in window.groups() if g))
        if prompt:
            self.prompt_tokens = int(next(g for g in prompt.groups() if g))
        return bool(prompt and self.context_window)

    def room(self) -> int | None:
        """Returns remaining output token capacity in the known context window."""
        return (
            self.context_window - self.prompt_tokens - CONTEXT_MARGIN
            if self.context_window
            else None
        )

    def output_limit(self) -> int:
        """Computes the max output tokens to request on the next completion call."""
        room = self.room()
        return (
            self.output_ceiling
            if room is None
            else max(MIN_OUTPUT, min(self.output_ceiling, room))
        )

    def compact_at(self) -> int:
        """Returns the prompt token threshold at which to trigger compaction."""
        if not self.context_window:
            return COMPACT_AT_TOKENS
        room = min(self.output_ceiling, self.context_window // 2)
        return max(
            self.context_window // 4,
            min(COMPACT_AT_TOKENS, self.context_window - room - CONTEXT_MARGIN),
        )

    def estimate_prompt_tokens(self) -> int:
        """Estimates prompt token count at four JSON characters per token."""
        return (
            sum(
                len(json.dumps({k: v for k, v in m.items() if k != "output_items"}))
                for m in self.messages
            )
            // 4
        )

    async def stream(
        self,
        messages: list[dict[str, Any]],
        tool_choice: str,
        reserve: float,
        head: str | None = None,
    ) -> Reply:
        """Streams a single chat completion call up to `reserve` seconds before end."""
        left = self.session.time_left()
        self.max_output = self.output_limit()
        reply = Reply()

        async def read():
            if self.responses:
                await self.respond(reply, messages, tool_choice)
                return
            stream = await client.chat.completions.create(
                model=MODEL,
                messages=marked(messages),
                tools=self.get_tools(),
                tool_choice=tool_choice,
                stream=True,
                stream_options={"include_usage": True},
                **self.effort,
                **{self.token_limit: self.max_output},
            )
            async for chunk in stream:
                reply.usage = chunk.usage or reply.usage
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                reply.finish = chunk.choices[0].finish_reason or reply.finish
                reply.text += delta.content or ""
                reply.reasoning += (
                    getattr(delta, "reasoning_content", None)
                    or getattr(delta, "reasoning", None)
                    or ""
                )
                reply.extra = merged(reply.extra, extra_fields(delta, DELTA_FIELDS))
                for part in delta.tool_calls or []:
                    reply.add_call(part)

        try:
            await asyncio.wait_for(read(), None if left is None else left - reserve)
        except (asyncio.TimeoutError, asyncio.CancelledError) as exc:
            if head is not None:
                self.session.final_message = (
                    visible(head + reply.text) or self.session.final_message
                )
            if isinstance(exc, asyncio.CancelledError):
                raise
            raise CutOff() from None
        except openai.APIError as exc:
            said = {
                "message": getattr(exc, "message", None) or str(exc),
                "type": getattr(exc, "type", None),
                "code": getattr(exc, "code", None),
            }
            if isinstance(exc, openai.APIStatusError) or isinstance(
                stream_error(said), StreamCut
            ):
                raise
            raise StreamBadRequest(said["message"]) from exc
        for n, call in reply.calls.items():
            call["id"] = call["id"] or f"call_{n}_{len(self.messages)}"
            call["name"] = call["name"].split("<|")[0].strip()
        return reply

    async def respond(
        self, reply: Reply, messages: list[dict[str, Any]], tool_choice: str
    ) -> None:
        """Streams a single Responses API call into `reply`."""
        effort = self.effort.get("reasoning_effort")
        stream = await client.responses.create(
            model=MODEL,
            input=response_input(messages),
            tools=[
                {"type": "function", **t["function"], "strict": False}
                for t in self.get_tools()
            ],
            tool_choice=tool_choice,
            stream=True,
            store=False,
            include=["reasoning.encrypted_content"],
            max_output_tokens=self.max_output,
            **({"reasoning": {"effort": effort}} if effort else {}),
        )
        async for event in stream:
            kind = getattr(event, "type", "")
            if kind == "response.output_text.delta":
                reply.text += event.delta or ""
            elif kind in ("error", "response.failed"):
                raise stream_error(
                    getattr(getattr(event, "response", None), "error", None) or event
                )
            elif kind in ("response.completed", "response.incomplete"):
                done = event.response
                items = [i.model_dump(exclude_none=True) for i in done.output or []]
                reply.extra = {"output_items": items}
                reply.text = "".join(
                    part.get("text", "")
                    for item in items
                    if item.get("type") == "message"
                    for part in item.get("content") or []
                    if part.get("type") == "output_text"
                )
                for item in items:
                    if item.get("type") == "function_call":
                        reply.calls[len(reply.calls)] = {
                            "id": item.get("call_id") or "",
                            "name": item.get("name") or "",
                            "arguments": item.get("arguments") or "",
                            "extra": {},
                            "function_extra": {},
                        }
                reply.usage = chat_usage(done.usage)
                reason = getattr(done.incomplete_details, "reason", None)
                if kind == "response.completed":
                    reply.finish = "tool_calls" if reply.calls else "stop"
                else:
                    reply.finish = reason if reason == "content_filter" else "length"

    async def record(self, reply: Reply) -> None:
        """Updates `prompt_tokens` from `reply` and reports token usage."""
        if reply.usage is None:
            self.prompt_tokens = self.estimate_prompt_tokens()
            return
        self.prompt_tokens = reply.usage.prompt_tokens or 0
        await self.report(reply)

    async def report(self, reply: Reply) -> None:
        """Reports token usage from `reply` to the evaluator session if present."""
        usage = reply.usage
        if usage is None:
            return
        cached = (
            getattr(
                getattr(usage, "prompt_tokens_details", None), "cached_tokens", 0
            )
            or 0
        )
        await self.session.usage(
            MODEL, usage.prompt_tokens or 0, usage.completion_tokens or 0, cached
        )

    async def run_tool(self, name: str, args: dict[str, Any]) -> str:
        """Dispatches a tool call by `name` and returns its clipped text output."""
        await self.session.log(f"{name} {json.dumps(args)[:400]}")
        try:
            if name == "mcp_call":
                name, args = str(args.get("tool", "")), args.get("arguments") or {}
                args = json.loads(args) if isinstance(args, str) else args
                if name not in self.mcp:
                    return f"error: no tool named {name!r}; use mcp_find"
            if name in self.mcp:
                server, t = self.mcp[name]
                return clip(await server.call(t["name"], args))
            if name == "mcp_find":
                return self.find_mcp(str(args.get("query", "")))
            handler = {
                "bash": self.bash,
                "read_file": self.read_file,
                "write_file": self.write_file,
                "edit_file": self.edit_file,
            }.get(name)
            return (
                clip(await handler(**args))
                if handler
                else f"error: there is no tool named {name}"
            )
        except taskbridge.TaskError as exc:
            return f"error: {exc}"
        except (
            AttributeError,
            KeyError,
            TypeError,
            ValueError,
            RuntimeError,
        ) as exc:
            return f"error: {type(exc).__name__}: {exc}"

    def path(self, path: str) -> str:
        """Resolves `path` relative to `self.session.workdir` if not absolute."""
        return (
            path
            if path.startswith("/")
            else posixpath.join(self.session.workdir, path)
        )

    async def bash(self, command: str, timeout_sec: int = 120) -> str:
        """Executes `command` with bash in the task container."""
        cap = int(self.session.limits.get("exec_timeout_sec") or 600)
        left = self.session.time_left()
        if left is not None:
            cap = min(cap, max(1, int(left - self.finish_margin)))
        result = await self.session.exec(
            command, taskbridge.positive_int(timeout_sec, 120, cap)
        )
        note = " (timed out)" if result.get("timed_out") else ""
        return (
            "exit code"
            f" {result['exit_code']}{note}\n{result['output'] or '(no output)'}"
        )

    async def read_file(self, path: str) -> str:
        """Reads a UTF-8 text file from `path` in the task container."""
        data = await self.session.read_file(self.path(path))
        if b"\0" in data[:8192]:
            return (
                f"{path} is a binary file ({len(data)} bytes); inspect it with bash"
                " (python3, unzip -l, ...)"
            )
        return data.decode("utf-8", "replace") or "(empty file)"

    async def write_file(
        self, path: str, content: str, append: bool = False
    ) -> str:
        """Writes or appends `content` to `path` in the task container."""
        size = await self.session.write_file(
            self.path(path), content, append=bool(append)
        )
        return f"{path} now holds {size} bytes"

    async def edit_file(
        self, path: str, old_text: str, new_text: str, replace_all: bool = False
    ) -> str:
        """Replaces `old_text` with `new_text` in `path` inside the task container."""
        text = (await self.session.read_file(self.path(path))).decode("utf-8")
        count = text.count(old_text) if old_text else 0
        if count == 0:
            return f"error: old_text was not found in {path}"
        if count > 1 and not replace_all:
            return (
                f"error: old_text occurs {count} times in {path}; add context to make"
                " it unique, or set replace_all"
            )
        await self.session.write_file(
            self.path(path),
            text.replace(old_text, new_text, -1 if replace_all else 1),
        )
        return f"replaced {count if replace_all else 1} occurrence(s) in {path}"

    def unread(self) -> list[dict[str, Any]]:
        """Returns tool result messages appended after the last assistant turn."""
        last = max(
            (n for n, m in enumerate(self.messages) if m["role"] == "assistant"),
            default=0,
        )
        return [m for m in self.messages[last:] if m["role"] == "tool"]

    async def compact(self, force: bool = False) -> bool:
        """Compacts conversation history without modifying unread tool results."""
        unread = {id(m) for m in self.unread()}
        results = [
            (n, m) for n, m in enumerate(self.messages) if m["role"] == "tool"
        ]
        cuts, size = [], max(
            self.estimate_prompt_tokens(), self.prompt_tokens if force else 0
        )
        for n, m in results if force else results[:-KEEP_RECENT_RESULTS]:
            if force and self.context_window and size <= self.compact_at():
                break
            if len(m["content"]) > 600 and id(m) not in unread:
                size -= (len(m["content"]) - 400) // 4
                m["content"] = (
                    m["content"][:400]
                    + "\n[... removed to save context; run the tool again if needed"
                    " ...]"
                )
                cuts.append(n)
        if cuts:
            await self.session.log(f"context: cut {len(cuts)} old tool results")
            self.prompt_tokens = self.estimate_prompt_tokens()
            if (
                not force
                or not self.context_window
                or self.prompt_tokens <= self.compact_at()
            ):
                return True
        cut = len(self.messages) - 6
        while cut > 3 and self.messages[cut]["role"] == "tool":
            cut -= 1
        if cut < 10:
            return bool(cuts)
        try:
            notes = await self.stream(
                self.messages[:cut] + [{"role": "user", "content": SUMMARY_PROMPT}],
                "none",
                self.finish_margin,
            )
        except (openai.APIError, StreamCut, asyncio.TimeoutError) as exc:
            await self.session.log(
                f"context: notes failed ({str(exc)[:200] or 'out of time'})"
            )
            return bool(cuts)
        await self.report(notes)
        if notes.finish is None:
            await self.session.log(
                "context: the notes were cut short, so the turns are kept"
            )
            return bool(cuts)
        text = visible(notes.text)
        if not text:
            await self.session.log(
                "context: the notes came back empty, so the turns are kept"
            )
            return bool(cuts)
        if notes.finish == "length":
            text += "\n[the notes were cut off at the output limit]"
        self.messages = (
            self.messages[:2]
            + [{
                "role": "user",
                "content": (
                    "Your notes on the work so far (earlier "
                    "turns were removed to save context):\n"
                    + text
                ),
            }]
            + self.messages[cut:]
        )
        await self.session.log(f"context: replaced {cut - 2} messages with notes")
        self.prompt_tokens = self.estimate_prompt_tokens()
        return True

    def cut_unread(self) -> bool:
        """Truncates unread tool results as a last resort when context is full."""
        unread = [m for m in self.unread() if len(m["content"]) > 2 * UNREAD_KEEP]
        if not unread:
            return False
        share = None
        if self.context_window:
            rest = (
                self.estimate_prompt_tokens()
                - sum(len(m["content"]) for m in unread) // 4
            )
            share = (self.compact_at() - rest) * 4 // len(unread)
        for m in unread:
            size = len(m["content"])
            keep = size // 2 if share is None or share >= size - 100 else share
            m["content"] = clip(m["content"], max(UNREAD_KEEP, keep))
        self.prompt_tokens = self.estimate_prompt_tokens()
        return True


async def run_planner(session: taskbridge.Session) -> str:
    """Runs the planner agent and returns the plan."""
    agent = Agent(session, role="planner")
    return await agent.run()


async def run_worker(session: taskbridge.Session, plan: str) -> str:
    """Runs the worker agent with the given plan and returns the summary."""
    agent = Agent(session, role="worker")
    task = session.instruction
    agent.messages = [
        {"role": "system", "content": agent.get_system_prompt("")},
        {"role": "user", "content": f"{task}\n\n## Plan\n{plan}"},
    ]
    return await agent.run()


async def run_verifier(session: taskbridge.Session, task: str, plan: str, summary: str) -> str:
    """Runs the verifier agent and returns the verdict."""
    agent = Agent(session, role="verifier")
    review = f"## Task\n{task}\n\n## Plan\n{plan}\n\n## The engineer's\nsummary\n{summary}"
    agent.messages = [
        {"role": "system", "content": agent.get_system_prompt("")},
        {"role": "user", "content": review},
    ]
    return await agent.run()


async def solve(session: taskbridge.Session) -> str:
    """Executes the planner, worker, and verifier loop for `session`."""
    total = session.time_left()

    def until(share):
        return 0 if total is None else total * share

    def time_for(wrap_up):
        left = session.time_left()
        return left is None or left - wrap_up >= MIN_STEP_SEC

    task = session.instruction
    plan = await run_planner(session)
    await session.log(f"plan: {plan[:1000]}")
    summary = await run_worker(session, plan)
    for _ in range(MAX_FIX_ROUNDS):
        if not time_for(until(CHECK_SHARE / 2)):
            break
        verdict = await run_verifier(session, task, plan, summary)
        await session.log(f"verifier: {verdict[:1000]}")
        if verdict.strip("*_. \r\n\t").upper() in ("", "PASS") or not time_for(
            WRAP_UP_SEC
        ):
            break
        # Add feedback to worker
        agent = Agent(session, role="worker")
        agent.messages = [
            {"role": "system", "content": agent.get_system_prompt("")},
            {"role": "user", "content": f"{task}\n\n## Plan\n{plan}"},
        ]
        # Replay the worker's conversation so far
        # This is a simplified approach - in practice we'd need to track the full conversation
        agent.messages.append({
            "role": "user",
            "content": (
                "A reviewer checked your files and found these"
                f" gaps:\n{verdict}\n\nFix them, then reply with your updated"
                " summary."
            ),
        })
        summary = (
            await agent.run() or summary
        )
    return summary or session.final_message


if __name__ == "__main__":
    taskbridge.run(solve)