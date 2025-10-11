import json
import re


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
    are on their own line (e.g., 'INTRO'). New lonely-line titles can be easily
    added to the `title_list` within the function.

    >>> text = "First sentence.\nFOCUS - The Economy\nSecond sentence.\n  Intro  \nThird sentence."
    >>> clean_titles(text)
    'First sentence.\n\nSecond sentence.\n\nThird sentence.'
    """
    # First, handle titles like "FOCUS - ..."
    focus_pattern = r'^FOCUS\s*-.*'
    text = re.sub(focus_pattern, '\n', transcript_text, flags=re.MULTILINE | re.IGNORECASE)

    # Next, handle titles that appear on their own line.
    # New titles can be easily added to this list.
    title_list = [
        'INTRO',
        'NEWSMAKER',
        'NEWS SUMMARY',
        'CONVERSATION',
        'BRIG\.',  # Escape dot for literal match
        'RECAP',
    ]
    # Create a regex pattern from the list: ^\s*(?:TITLE1|TITLE2|...)\s*$
    titles_pattern = r'^\s*(?:' + '|'.join(title.replace(' ', r'\s+') for title in title_list) + r')\s*$'
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

    >>> clean_speakers("\nROBERT MacNEIL: This is a test.")
    ' This is a test.'
    >>> clean_speakers("This is a sentence. LEHRER: And another one.")
    'This is a sentence.\nAnd another one.'
    >>> clean_speakers("\nMR. LEHRER: A third example.")
    ' A third example.'
    >>> clean_speakers("\nSTUDENT #2: I have a question.")
    ' I have a question.'
    >>> clean_speakers("Then KANG SHI`EN: said something.")
    'Then\nsaid something.'
    >>> clean_speakers("A sentence that is NOT A SPEAKER:")
    'A sentence that is NOT A SPEAKER:'
    """
    speaker_intro = r'(?<=[A-Z]),\s[a-zA-Z\.\'-,\s]*(?=:)'
    text = re.sub(speaker_intro, "", transcript_text)

    speaker_titles = r'(?<=\n)(?i:Rep\.|Dr\.|Sen\.|Mr\.|Ms\.|Mrs\.|Prof\.|Pres\.)\s'
    text = re.sub(speaker_titles, "", text)

    # remove the speaker's name using newline
    newline_speaker = r'\n([A-Za-z\d\'\"`#\-]+\s){0,3}[A-Za-z\d\'\"`#\-]+:'
    text = re.sub(newline_speaker, " ", text)

    # remove the speaker's name inline
    speaker_name_inline = r'(?=[\.\?\-\s])\s(?:([A-Za-z\d\'\"`#\-]+\s){0,3}[A-Za-z\d\'\"`#\-]+):(?!\.)'
    text = re.sub(speaker_name_inline, "\n", text)

    # remove the speaker's title inline
    speaker_title_inline = r'(?i:Rep\.|Dr\.|Sen\.|Mr\.|Ms\.|Mrs\.|Prof\.|Pres\.|Gen\.)(?=\n)'
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
