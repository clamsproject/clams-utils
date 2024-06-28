import os
import re
import argparse

def extract_text(original_transcript_path, cleaned_transcript_path):
    if not os.path.exists(cleaned_transcript_path):
        os.makedirs(cleaned_transcript_path)
    for filename in os.listdir(original_transcript_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(original_transcript_path, filename)
            with open(file_path, 'r') as f:
                text = f.read()
            if "{" not in text:
                speakers_removed_text = replace_matched_words(text)
                new_transcript_file = os.path.join(cleaned_transcript_path, filename)
                with open(new_transcript_file, 'w') as f:
                    f.write(speakers_removed_text)

def replace_matched_words(text):
    pattern1 = r'\s\[.*\]'
    square_bracket_removed = re.sub(pattern1, " ", text)
    pattern2 = r'[A-Z],\s[a-zA-Z\.\'-,\s]*(?=:)'
    speaker_position_removed = re.sub(pattern2, " ", square_bracket_removed)
    pattern3 = r'\n[A-Z][a-zA-Z\s\'\.-]*[A-Z\s]:(?!\.)'
    newline_speaker_removed = re.sub(pattern3, " ", speaker_position_removed)
    pattern4 = r'(?=[\.\?\-\s])\s[A-Z][a-zA-Z\s\'-]*[A-Z\s]:(?!\.)'
    speaker_removed = re.sub(pattern4, " ", newline_speaker_removed)
    return speaker_removed

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--transcriptPath", action='store', help="path to the directory of all text files")
    parser.add_argument("--cleanTranscriptPath", action='store', help="path to the directory of cleaned transcripts")
    parsed_args = parser.parse_args()
    extract_text(parsed_args.transcriptPath, parsed_args.cleanTranscriptPath)
