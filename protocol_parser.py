"""
protocol_parser.py
════════════════════════════════════════════════════════════════════
Shared parser for the Mixtral/Dex tool-call protocol.

The model is expected to emit tool calls like:

    //tool="message" value="Hello there"
    //tool="cmd_exec" head="run" value="notepad.exe"

PROBLEM THIS FIXES:
The old regex (duplicated in main_ui.py x2 and port.py x1) required the
leading slashes to sit *immediately* next to `tool=` with zero whitespace
or newlines in between, e.g. it matched `//tool=` but NOT:

    // tool=
    //
    tool=
    /
    /tool=

Different backends (Gemini vs. local Ollama models) are not consistent
about whitespace/line breaks around the marker, quote style (straight vs.
curly/smart quotes), or spacing around `=`. When the marker didn't match,
the raw slashes + tool syntax leaked straight into the chat bubble instead
of being parsed out and hidden.

This module is the single source of truth for parsing that protocol, so
the UI and the execution engine can never drift out of sync again.
"""

import re

# Any straight or "smart"/curly quote character the model might use.
_QUOTE = r'["\'\u201c\u201d\u2018\u2019]'
_QUOTE_CLASS = r'["\'\u201c\u201d\u2018\u2019]'

# A "marker" = optional junk (whitespace/dash/pipe), THEN at least one
# slash/backslash, THEN more optional junk/slashes/whitespace/newlines,
# THEN "tool", THEN optional whitespace, THEN "=".
# This tolerates the marker being split across lines or padded with spaces.
_MARKER = r'[\s\-\|]*[/\\][\s\-\|/\\]*'

# Lookahead used to split raw text into per-tool-call chunks.
_SPLIT_RE = re.compile(rf'(?i)(?={_MARKER}tool\s*=)')

# Confirms a chunk IS a tool block (as opposed to plain prose).
_IS_TOOL_RE = re.compile(rf'(?i)^{_MARKER}tool\s*=')

_TOOL_RE = re.compile(rf'(?i)tool\s*=\s*{_QUOTE_CLASS}([^"\'\u201c\u201d\u2018\u2019]+){_QUOTE_CLASS}')
_HEAD_RE = re.compile(rf'(?i)head\s*=\s*{_QUOTE_CLASS}([^"\'\u201c\u201d\u2018\u2019]*){_QUOTE_CLASS}')
_VALUE_RE = re.compile(rf'(?i)value\s*=\s*{_QUOTE_CLASS}([\s\S]*){_QUOTE_CLASS}')

# Lines made ONLY of decorative junk (spinner remnants / stray leftover
# slashes that weren't part of a real tool marker).
_JUNK_LINE_RE = re.compile(r'(?m)^[\s/\\\-\|]+$')
_MULTI_BLANK_RE = re.compile(r'\n{3,}')

DEFAULT_MESSAGE_TOOLS = ("message", "msg", "reply")


def _normalize_quotes(s: str) -> str:
    return (
        s.replace('\u201c', '"').replace('\u201d', '"')
         .replace('\u2018', "'").replace('\u2019', "'")
    )


def parse_tool_chunk(chunk: str):
    """
    Try to parse a single chunk as one tool call.
    Returns (tool, head, value, trailing_text) or None if not a tool block.
    """
    chunk = chunk.strip()
    if not _IS_TOOL_RE.match(chunk):
        return None

    tool_match = _TOOL_RE.search(chunk)
    val_match = _VALUE_RE.search(chunk)
    if not tool_match or not val_match:
        return None

    head_match = _HEAD_RE.search(chunk)

    tool = tool_match.group(1).strip()
    head = head_match.group(1).strip() if head_match else ""
    raw_value = val_match.group(1)

    value = raw_value.replace('\\"', '"').replace('\\\\', '\\').strip()
    trailing = chunk[val_match.end():].strip()

    return tool, head, value, trailing


def split_protocol(raw_text: str):
    """
    Split raw model output into an ordered list of tuples:
        ('tool', tool_name, head, value)
        ('text', plain_text)
    """
    if not raw_text:
        return []

    # IMPORTANT: do NOT strip decorative slash-only lines before splitting.
    # Those slashes may be part of a legitimate (just oddly-formatted)
    # tool marker, and stripping them here would delete the marker before
    # the splitter ever gets to see it -- which was the original bug.
    # Junk-line cleanup instead runs only on chunks that turn out to be
    # plain prose (see the `else` branch below).
    normalized = _normalize_quotes(raw_text)
    clean_text = _MULTI_BLANK_RE.sub('\n\n', normalized).strip()

    chunks = _SPLIT_RE.split(clean_text)
    items = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        parsed = parse_tool_chunk(chunk)
        if parsed:
            tool, head, value, trailing = parsed
            items.append(('tool', tool, head, value))
            if trailing:
                items.append(('text', trailing))
        else:
            # Not a recognized tool block -> plain prose. Strip any
            # leftover decorative junk lines just in case.
            residual = _JUNK_LINE_RE.sub('', chunk).strip()
            if residual:
                items.append(('text', residual))
    return items


def build_display_text(raw_text: str,
                        message_tools=DEFAULT_MESSAGE_TOOLS,
                        fallback: str = "✅ Action executed successfully.") -> str:
    """
    UI-facing helper: turn raw model output into what should be shown in
    the chat bubble. Tool calls are hidden except message/msg/reply tools,
    whose `value` is surfaced as the visible message text.
    """
    parts = []
    for item in split_protocol(raw_text):
        if item[0] == 'tool':
            _, tool, head, value = item
            if tool.lower() in message_tools:
                parts.append(value)
            # other tools (canvas, cmd_exec, etc.) are intentionally hidden
        else:
            parts.append(item[1])

    display_text = "\n\n".join(p for p in parts if p).strip()
    return display_text or fallback
