import json
import pathlib
import re

import dirs

suffix = '-transcript'


def extract_text(gbh_json_dir):
    for j in pathlib.Path(gbh_json_dir).glob('*.json'):
        guid = j.name.split('.')[0][:len(suffix) * -1]
        if guid in dirs.exclude_guid:
            continue
        with open(j, 'r') as f:
            data = json.load(f)
        # print(guid, data.keys())

        sentences = []
        # if data['parts']:
        for i in range(len(data['parts'])):
            sentences.append(data['parts'][i]['text'])

        text = ' '.join(sentences)

        dirs.gold_texts_dir.mkdir(parents=True, exist_ok=True)
        with (open(dirs.gold_texts_dir / f'{guid}{suffix}.txt', 'w', encoding='utf-8') as txt):
            # exising regex
            text = re.sub("[\<\[].*?[\>\]]", "", text)
            # new regex to remove parens
            text = re.sub("\((.*?)\)","",text)
            # new regex to remove '^[:. ]+'
            text = re.sub("^[:. ]+", "", text)

            txt.write(text)
            # txt.close()
        # else:
        # 	for i in range(len(data['phrases'])):
        # 		sentences.append(data['phrases'][i]['text'])

        # 	text = ' '.join(sentences)

        # 	with open ('./gold_texts/'+id+'.txt', 'w', encoding='utf-8') as txt:
        # 		txt.write(text)
    
if __name__ == '__main__':
    extract_text(dirs.gold_jsons_dir)
