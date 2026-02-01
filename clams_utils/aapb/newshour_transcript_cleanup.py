import json
import re
from typing import List, Tuple

# =============================================================================
# Shared constants for NewsHour transcript processing
# =============================================================================

# Section titles that appear on their own line (not speaker markers)
SECTION_TITLES = [
    'INTRO',
    'NEWSMAKER',
    'NEWS SUMMARY',
    'CONVERSATION',
    'BRIG.',
    'RECAP',
]

# Titles that precede speaker names
DOTTED_TITLES = [
    'Dr.', 'Mr.', 'Ms.', 'Mrs.', 'Prof.', 'Pres.', 'Gen.',
    'Rep.', 'Sen.', 'Gov.']
MORE_TITLES = [
    'Mayor', 'President', 'Secretary']
SPEAKER_TITLES = DOTTED_TITLES + MORE_TITLES

# Pattern to match speaker markers at start of line
# Handles: "ROBERT MacNEIL:", "Dr. HELEN SINGER KAPLAN:",
#          "Rep. JIM LEACH, (R) Iowa:", "Mayor ED KOCH, (D) New York [August 30, 1985]:"
#          "CROSS [voice-over]:", "Gov. WILKINSON [July 1985]:"
#
# IMPORTANT: Use [ ] (literal space) instead of \s to avoid matching across newlines
_SPEAKER_TITLES_PATTERN = '|'.join(re.escape(t) for t in SPEAKER_TITLES)
SPEAKER_MARKER_PATTERN = re.compile(
    r'^'                                      # Start of line
    r'('                                      # Capture group 1: speaker name
    r'(?:'                                    # Optional title prefix
    r'(?:' + _SPEAKER_TITLES_PATTERN + r')[ ]+'
    r')?'
    r"[A-Z][A-Za-z \.'\-]+"                   # Name: uppercase start, mixed case allowed
    r')'                                      # End capture group
    r'(?:'                                    # Optional annotations (non-capturing)
    r',[ ]*\([^)]+\)[^:\[\]]*'                # Like ", (D) New York"
    r'|'
    r'[ ]*\[[^\]]+\]'                         # Like " [voice-over]" or " [July 1985]"
    r')*'
    r':'                                      # Colon after speaker name
    r'[ ]*',                                  # Optional spaces (not newlines)
    re.MULTILINE
)


# =============================================================================
# Speaker extraction (for speaker diarization)
# =============================================================================

def normalize_speaker_name(name: str) -> str:
    """
    Normalize speaker name for use as speaker-id.
    Strips whitespace and replaces spaces with underscores.

    >>> normalize_speaker_name("ROBERT MacNEIL")
    'ROBERT_MacNEIL'
    >>> normalize_speaker_name("Dr. HELEN SINGER KAPLAN ")
    'Dr._HELEN_SINGER_KAPLAN'
    """
    return name.strip().replace(' ', '_')


def extract_speaker_spans(transcript_text: str) -> List[Tuple[str, int, int]]:
    """
    Extract speaker spans with character positions from a transcript.

    Each span represents a contiguous region of text spoken by one speaker.
    The character offsets point into the original transcript text.

    :param transcript_text: The full text of a NewsHour transcript
    :returns: List of tuples (speaker_id, start_char, end_char) where:

        - speaker_id: Normalized speaker name (spaces replaced with underscores)
        - start_char: Character offset where speaker's content begins (after "NAME: ")
        - end_char: Character offset where speaker's content ends (exclusive)

    >>> text = "Intro\\n\\nROBERT MacNEIL: Hello.\\n\\nJUDY WOODRUFF: Hi."
    >>> spans = extract_speaker_spans(text)
    >>> [(s, text[start:end].strip()[:10]) for s, start, end in spans]
    [('ROBERT_MacNEIL', 'Hello.'), ('JUDY_WOODRUFF', 'Hi.')]
    """
    spans = []
    last_speaker = None
    last_content_start = None

    for match in SPEAKER_MARKER_PATTERN.finditer(transcript_text):
        speaker_name = match.group(1).strip()
        content_start = match.end()  # Content starts after "NAME: "

        # Close the previous speaker's span
        if last_speaker is not None:
            content_end = match.start()
            spans.append((last_speaker, last_content_start, content_end))

        last_speaker = normalize_speaker_name(speaker_name)
        last_content_start = content_start

    # Don't forget the last speaker
    if last_speaker is not None:
        spans.append((last_speaker, last_content_start, len(transcript_text)))

    return spans


def split_by_speakers(
    speaker_spans: List[Tuple[str, int, int]],
    char_start: int,
    char_end: int
) -> List[Tuple[str, int, int]]:
    """
    Return split of the query character range by speakers. 
    If the range is spoken only by one speaker, returns an empty list.

    :param speaker_spans: List of (speaker_id, start_char, end_char) from extract_speaker_spans
    :param char_start: Start of query range
    :param char_end: End of query range (exclusive)
    :returns: List of (speaker_id, start, end) for split spans
    """
    splits = []
    for speaker_id, span_start, span_end in speaker_spans:
        if span_end <= char_start or span_start >= char_end:
            continue
        start = max(span_start, char_start)
        end = min(span_end, char_end)
        splits.append((speaker_id, start, end))
    return splits


# =============================================================================
# Transcript cleanup (for ASR evaluation, etc.)
# =============================================================================

def json_cleaner(transcript_json):
    """
    Given a JSON object read from a file, extract the text and clean it from the file.
    If the file has no field of "text", return None
    """
    try:
        sentences = []
        for i in range(len(transcript_json['parts'])):
            sentences.append(transcript_json['parts'][i]['text'])
        return clean(' '.join(sentences))
    except KeyError:
        return None


def clean(transcript_text):
    """
    Given a plain text read from a txt file,
    extract texts by removing unspoken words,
    including speakers' names, descriptions in brackets, and news section titles
    """
    return '\n'.join((line.strip() for line in clean_speakers(clean_brackets(clean_titles(transcript_text))).splitlines()))


def clean_titles(transcript_text):
    """
    Given a plain text read from a txt file, clean the news section titles in the transcript.
    It handles titles that span a whole line (e.g., 'FOCUS - ...') and titles that
    are on their own line (e.g., 'INTRO'). New titles can be added to SECTION_TITLES.

    >>> text = "First sentence.\nFOCUS - The Economy\nSecond sentence.\n  Intro  \nThird sentence."
    >>> clean_titles(text)
    'First sentence.\n\nSecond sentence.\n\nThird sentence.'
    """
    # First, handle titles like "FOCUS - ..."
    focus_pattern = r'^FOCUS\s*-.*'
    text = re.sub(focus_pattern, '\n', transcript_text, flags=re.MULTILINE | re.IGNORECASE)

    # Handle titles that appear on their own line (uses shared SECTION_TITLES constant)
    # Escape special regex chars and replace spaces with \s+
    escaped_titles = [re.escape(t).replace(r'\ ', r'\s+') for t in SECTION_TITLES]
    titles_pattern = r'^\s*(?:' + '|'.join(escaped_titles) + r')\s*$'
    text = re.sub(titles_pattern, '\n', text, flags=re.MULTILINE | re.IGNORECASE)

    return text


def clean_brackets(transcript_text):
    """
    Given a plain text read from a txt file, clean the text with brackets,
    including square brackets and parentheses.

    >>> clean_brackets("This is a sentence [with some bracketed text] and another (with more).")
    'This is a sentence and another.'
    >>> clean_brackets("A sentence with (one) and (two) bracketed parts.")
    'A sentence with and bracketed parts.'
    """
    brackets = r'\s[\[\(].*?[\]\)]'
    brackets_removed = re.sub(brackets, "", transcript_text)

    return brackets_removed


def clean_speakers(transcript_text):
    """
    Given a plain text read from a txt file, clean speakers' names in the transcript.
    This can be their last name, full name, names with titles (e.g., Prof., Mr., Sen.),
    and names with a short intro on who they are (e.g., WALTER MONDALE, Democratic presidential candidate).
    Handles various formats including all-caps names, mixed-case names (e.g., MacNEIL),
    and names with titles. It also handles names with numbers and various quotation marks.

    >>> clean_speakers("\\nROBERT MacNEIL: This is a test.")
    ' This is a test.'
    >>> clean_speakers("This is a sentence. LEHRER: And another one.")
    'This is a sentence.\\nAnd another one.'
    >>> clean_speakers("\\nMR. LEHRER: A third example.")
    ' A third example.'
    >>> clean_speakers("\\nSTUDENT #2: I have a question.")
    ' I have a question.'
    >>> clean_speakers("Then KANG SHI`EN: said something.")
    'Then\\nsaid something.'
    >>> clean_speakers("A sentence that is NOT A SPEAKER:")
    'A sentence that is NOT A SPEAKER:'
    """
    # Remove speaker introductions like ", Democratic presidential candidate"
    speaker_intro = r'(?<=[A-Z]),\s[a-zA-Z\.\'-,\s]*(?=:)'
    text = re.sub(speaker_intro, "", transcript_text)

    # Build pattern for titles that have dots (need escaping)
    speaker_titles_pattern = r'(?<=\n)(?i:' + '|'.join(DOTTED_TITLES) + r')\s'
    text = re.sub(speaker_titles_pattern, "", text)

    # Remove the speaker's name at start of line
    newline_speaker = r'\n([A-Za-z\d\'\"`#\-]+\s){0,3}[A-Za-z\d\'\"`#\-]+:'
    text = re.sub(newline_speaker, " ", text)

    # Remove the speaker's name inline (after punctuation)
    speaker_name_inline = r'(?=[\.\?\-\s])\s(?:([A-Za-z\d\'\"`#\-]+\s){0,3}[A-Za-z\d\'\"`#\-]+):(?!\.)'
    text = re.sub(speaker_name_inline, "\n", text)

    # Remove leftover speaker titles at end of line
    speaker_title_inline = r'(?i:' + '|'.join(DOTTED_TITLES) + r')(?=\n)'
    text = re.sub(speaker_title_inline, "", text)

    return text


def is_json(in_file):
    """
    Given an input file, check if it is a JSON file or a JSON-like txt file.
    """
    if in_file.endswith('.json'):
        return True
    elif in_file.endswith('.txt'):
        with open(in_file, 'r') as f:
            text = f.read().strip()
        if text.startswith("{") and text.endswith("}"):
            return True
    else:
        return False


def file_cleaner(dirty_transcript_file):
    """
    Given an input dirty transcript file (.txt or .json),
    cleans the transcript.
    Returns the extracted/cleaned text.
    """
    if is_json(dirty_transcript_file):
        with open(dirty_transcript_file, 'r') as f:
            text = f.read()
            transcript_json = json.loads(text)
        text = json_cleaner(transcript_json)
    else:
        with open(dirty_transcript_file, 'r') as f:
            transcript_text = f.read()
        text = clean("\n" + transcript_text)

    return text


def clean_and_write(indir, outdir):
    """
    Given a directory with all dirty transcripts,
    cleans all the transcripts, and store the cleaned files into a new directory
    """
    from pathlib import Path
    indir = Path(indir).expanduser()
    outdir = Path(outdir).expanduser()
    outdir.mkdir(parents=True, exist_ok=True)
    for in_file in indir.glob("*"):
        if in_file.suffix not in (".json", ".txt"):
            continue
        out_file = outdir / in_file.with_suffix(".txt").name
        text = file_cleaner(str(in_file))
        if text is not None:
            with open(out_file, 'w') as f:
                f.write(text)


CMD_NAME = 'cleanup'


def prep_argparser(subparsers):
    """
    Prepare the argument parser for the cleanup command.
    """
    cleanup_parser = subparsers.add_parser(
        CMD_NAME,
        description="Clean a Newshour transcript file or a directory of files.",
        help="Clean a Newshour transcript file or a directory of files."
    )
    cleanup_parser.add_argument("indir", help="input file or directory")
    cleanup_parser.add_argument("outdir", help="output directory")
    cleanup_parser.set_defaults(func=main)


def main(args):
    """
    Main function for the cleanup command.
    """
    clean_and_write(args.indir, args.outdir)
