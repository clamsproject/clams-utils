import os
import json
import re

def extract_text_from_json(transcript_json):
    """
    Given a JSON object read from a file, extract the text from the file.
    If the file has no field of "text", return None
    """
    sentences = []
    try:
        for i in range(len(transcript_json['parts'])):
            sentences.append(transcript_json['parts'][i]['text'])
        text = ' '.join(sentences)
    except KeyError:
        text = None
    return text
def extract_text_from_plain_text(transcript_text):
    """
    Given a plain text read from a txt file, extract texts by removing speakers' names
    """
    titles_removed = clean_titles(transcript_text)
    brackets_removed = clean_brackets(titles_removed)
    speakers_removed = clean_speakers(brackets_removed)
    return speakers_removed

def clean_titles(transcript_text):
    """
    Given a plain text read from a txt file, clean the titles in the transcript,
    including "Focus", "Intro", and "News Summary"
    """
    focus = r'^FOCUS-.*\n'
    focus_removed = re.sub(focus, '\n', transcript_text)

    intro = r'\nI(?i:ntro)[\n\s]'
    intro_removed = re.sub(intro, '\n', focus_removed)

    newsmaker = r'\nN(?:ewsmaker)\n'
    newsmaker_removed = re.sub(newsmaker, '\n', intro_removed)

    news_summary = r'(?<=\s|\n)N(?i:ews)\s(?i:summary)(?=\n)'
    all_titles_removed = re.sub(news_summary, '\n', newsmaker_removed)

    return all_titles_removed

def clean_brackets(transcript_text):
    """
    Given a plain text read from a txt file, clean the text with brackets,
    including square brackets and parentheses
    """
    brackets = r'\s[\[\(].*[\]\)]'
    brackets_removed = re.sub(brackets, "", transcript_text)

    return brackets_removed

def clean_speakers(transcript_text):
    """
    Given a plain text read from a txt file, clean speakers' names in the transcript.
    This can be their last name, full name, names with titles (e.g., Prof., Mr., Sen.),
    and names with a short intro on who they are (e.g., WALTER MONDALE, Democratic presidential candidate)
    """
    speaker_intro = r'(?<=[A-Z]),\s[a-zA-Z\.\'-,\s]*(?=:)'
    text = re.sub(speaker_intro, "", transcript_text)

    speaker_titles = r'(?<=\n)(?i:Rep\.|Dr\.|Sen\.|Mr\.|Ms\.|Mrs\.|Prof\.|Pres\.)(?=\s)'
    text = re.sub(speaker_titles, "", text)

    # remove the speaker's name using newline
    newline_speaker = r'\n[A-Z][a-zA-Z\s\'\.\-]*[A-Z]:'
    text = re.sub(newline_speaker, " ", text)

    # remove the speaker's name inline
    speaker_name_inline = r'(?=[\.\?\-\s])\s[A-Z][a-zA-Z\s\'-]*[A-Z]:(?!\.)'
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

def extract_text(in_file, out_file):
    """
    Given an input file, extract the text from the file, and write it to an output file.
    """
    if is_json(in_file):
        with open(in_file, 'r') as f:
            text = f.read()
            transcript_json = json.loads(text)
        text = extract_text_from_json(transcript_json)
    else:
        with open(in_file, 'r') as f:
            transcript_text = f.read()
        text = extract_text_from_plain_text("\n" + transcript_text)
    if text is not None:
        with open(out_file, 'w') as f:
            f.write(text)

def clean(transcript_path, cleaned_transcript_path):
    if not os.path.exists(cleaned_transcript_path):
        os.makedirs(cleaned_transcript_path)
    for file in os.listdir(transcript_path):
        in_file = os.path.join(transcript_path, file)
        if file.endswith(".txt"):
            out_file = os.path.join(cleaned_transcript_path, file)
        elif file.endswith(".json"):
            out_file = os.path.join(cleaned_transcript_path, file.replace(".json", ".txt"))
        else:
            continue
        extract_text(in_file, out_file)
