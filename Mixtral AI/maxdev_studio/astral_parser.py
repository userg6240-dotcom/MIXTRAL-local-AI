import re

def parse_protocol(raw_text: str):
    """
    Robust protocol parser designed for code payloads.
    Ignores inner quotes/apostrophes and reads to the true boundary of value="...".
    """
    if not raw_text:
        return []

    results = []
    
    # Locate all tool markers in the raw text stream
    tool_start_pattern = re.compile(
        r'(?:/\\/\\|//|/)\s*tool\s*=\s*["\u201c]([^"\u201d]+)["\u201d]',
        re.IGNORECASE
    )
    
    matches = list(tool_start_pattern.finditer(raw_text))
    if not matches:
        text_clean = raw_text.strip()
        if text_clean:
            results.append(('text', text_clean))
        return results

    last_idx = 0
    for i, match in enumerate(matches):
        # Capture any leading text before the tool call
        if match.start() > last_idx:
            lead = raw_text[last_idx:match.start()].strip()
            if lead:
                results.append(('text', lead))

        tool_name = match.group(1).strip()
        sub_str = raw_text[match.end():]
        
        # Check for optional head="..." attribute
        head_val = ""
        head_match = re.match(
            r'^\s*head\s*=\s*["\u201c](.*?)["\u201d]',
            sub_str,
            re.IGNORECASE
        )
        val_search_start = match.end()
        if head_match:
            head_val = head_match.group(1)
            val_search_start += head_match.end()

        # Find the start of value="..."
        val_kw_match = re.search(r'\bvalue\s*=\s*["\u201c]', raw_text[val_search_start:], re.IGNORECASE)
        if not val_kw_match:
            last_idx = match.start() + 1
            continue

        val_payload_start = val_search_start + val_kw_match.end()
        
        # Determine boundary limit using the next tool marker or end of string
        next_tool_pos = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
        candidate_chunk = raw_text[val_payload_start:next_tool_pos]
        
        # Find the true closing quote of the value attribute right before the next tool/end
        last_quote_idx = candidate_chunk.rfind('"')
        if last_quote_idx == -1:
            last_quote_idx = candidate_chunk.rfind('”')
            
        if last_quote_idx != -1:
            payload = candidate_chunk[:last_quote_idx]
            last_idx = val_payload_start + last_quote_idx + 1
        else:
            payload = candidate_chunk.strip()
            if payload.endswith('"') or payload.endswith('”'):
                payload = payload[:-1]
            last_idx = next_tool_pos

        # Safely unescape python escape sequences
        if payload:
            payload = (payload
                       .replace(r'\n', '\n')
                       .replace(r'\t', '\t')
                       .replace(r'\"', '"')
                       .replace(r"\'", "'")
                       .replace(r'\\', '\\'))

        results.append(('tool', tool_name, head_val, payload))

    # Capture any trailing text response
    if last_idx < len(raw_text):
        tail = raw_text[last_idx:].strip()
        if tail:
            results.append(('text', tail))

    return results