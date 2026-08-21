import re


def clean_extracted_text(text: str) -> str:
    """
    Cleans raw extracted text from PDF or OCR.
    - Removes non-printable ASCII/Unicode control characters (except newline, tab).
    - Replaces consecutive horizontal spaces with a single space.
    - Normalizes multi-line spacing to prevent excessive empty lines.
    - Trims leading/trailing line whitespace.
    """
    if not text:
        return ""

    # Remove non-printable control characters (keeping \n and \t)
    cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', text)

    # Normalize carriage returns to standard newlines
    cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')

    # Trim trailing whitespace on each line
    lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in cleaned.split('\n')]

    # Collapse more than 2 consecutive blank lines into a single blank line
    result_lines = []
    blank_count = 0
    for line in lines:
        if not line:
            blank_count += 1
            if blank_count <= 2:
                result_lines.append("")
        else:
            blank_count = 0
            result_lines.append(line)

    return "\n".join(result_lines).strip()
