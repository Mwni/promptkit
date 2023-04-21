import requests
import json


class OpenAIChat:
	def __init__(self, api_key, model='gpt-3.5-turbo', **config):
		self.api_key = api_key
		self.model = model
		self.config = config


	def __call__(self, messages):
		r = requests.post(
			'https://api.openai.com/v1/chat/completions' , 
			headers={
				'Content-Type': 'application/json',
				'Authorization': 'Bearer %s' % self.api_key
			}, 
			data=json.dumps({
				'messages': [{'role': m.role, 'content': m.text} for m in messages], 
				'model': self.model,
				**self.config
			})
		)

		data = json.loads(r.text)

		try:
			return data['choices'][0]['message']['content'].strip()
		except:
			if 'error' in data:
				raise Exception(data['error']['message'])

			raise Exception('empty-response')
