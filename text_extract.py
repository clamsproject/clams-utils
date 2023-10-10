import json
import os


gold_dir = '.'
gold_texts = os.listdir(gold_dir)

for gold_text in gold_texts:
	if gold_text.endswith('.json'):
		id = gold_text.split('.')[0]
		# print(id)

		with open (gold_text, 'r') as f:
			data = json.load(f)

		sentences = []
		# if data['parts']:
		for i in range(len(data['parts'])):
			sentences.append(data['parts'][i]['text'])

		text = ' '.join(sentences)

		with open ('./gold_texts/'+id+'.txt', 'w', encoding='utf-8') as txt:
  			txt.write(text)
  			# txt.close()
		# else:
		# 	for i in range(len(data['phrases'])):
		# 		sentences.append(data['phrases'][i]['text'])

		# 	text = ' '.join(sentences)

		# 	with open ('./gold_texts/'+id+'.txt', 'w', encoding='utf-8') as txt:
  		# 		txt.write(text)
