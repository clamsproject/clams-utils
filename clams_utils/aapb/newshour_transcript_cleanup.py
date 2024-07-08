import os
import argparse

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
    # remove titles that are 'FOCUS'
    focus = r'^FOCUS-.*\n'
    focus_removed = re.sub(focus, '\n', transcript_text)
    # remove titles that are 'Intro', usually showing up at the beginning of a transcript
    intro = r'\nI(?i:ntro)[\n\s]'
    intro_removed = re.sub(intro, '\n', focus_removed)
    # remove titles that are 'News summary', which can show up in either upper or lower cases
    news_summary = r'(?<=\s|\n)N(?i:ews)\s(?i:summary)(?=\n)'
    news_summary_removed = re.sub(news_summary, '\n', intro_removed)
    # remove parenthesis and square brackets, which are usually unspoken words
    brackets = r'\s[\[\(].*[\]\)]'
    square_bracket_removed = re.sub(brackets, " ", news_summary_removed)
    # remove the position of the speaker, usually appears after their names and before the column (e.g., "WALTER MONDALE, Democratic presidential candidate:")
    speaker_position = r'[A-Z],\s[a-zA-Z\.\'-,\s]*(?=:)'
    speaker_position_removed = re.sub(speaker_position, " ", square_bracket_removed)
    # remove the speaker's title (e.g., Mr., Prof., Sen.)
    newline_speaker_title = r'(?<=\n)(Rep\.|Dr\.|Sen\.|Mr\.|Ms\.|Mrs\.|Prof\.|Pres\.)(?=\s)'
    newline_speaker_title_removed = re.sub(newline_speaker_title, '', speaker_position_removed)
    # remove the speaker's name using newline
    newline_speaker = r'(?=\n)[A-Z][a-zA-Z\s\'\.-]*[A-Z\s]:(?!\.)'
    newline_speaker_removed = re.sub(newline_speaker, " ", newline_speaker_title_removed)
    # remove unprocessed names
    speaker_name = r'(?=[\.\?\-\s])\s[A-Z][a-zA-Z\s\'-]*[A-Z\s]:(?!\.)'
    speaker_name_removed = re.sub(speaker_name, " ", newline_speaker_removed)
    return speaker_name_removed

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

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--transcriptPath", action='store', help="path to the directory of all text files")
    parser.add_argument("--cleanTranscriptPath", action='store', help="path to the directory of cleaned transcripts")
    parsed_args = parser.parse_args()
    if not os.path.exists(parsed_args.cleanTranscriptPath):
        os.makedirs(parsed_args.cleanTranscriptPath)
    for file in os.listdir(parsed_args.transcriptPath):
        in_file = os.path.join(parsed_args.transcriptPath, file)
        if file.endswith(".txt"):
            out_file = os.path.join(parsed_args.cleanTranscriptPath, file)
        elif file.endswith(".json"):
            out_file = os.path.join(parsed_args.cleanTranscriptPath, file.replace(".json", ".txt"))
        else:
            continue
        extract_text(in_file, out_file)
