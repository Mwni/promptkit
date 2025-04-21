import requests
import json
from ..messages import AssistantMessage
from .base import BaseLLM

class OpenAIChat(BaseLLM):
	def __init__(self, api_key, base_url='https://api.openai.com/v1/chat/completions', model='gpt-3.5-turbo', **config):
		self.api_key = api_key
		self.base_url = base_url
		self.model = model
		self.config = config


	def __call__(self, messages, **config):
		r = requests.post(
			self.base_url, 
			headers={
				'Content-Type': 'application/json',
				'Authorization': 'Bearer %s' % self.api_key
			},
			data=json.dumps({
				'messages': [{'role': m.role, 'content': m.text} for m in messages], 
				'model': self.model,
				**self.config,
				**config
			})
		)

		data = json.loads(r.text)

		try:
			return AssistantMessage(text=data['choices'][0]['message']['content'])
		except:
			if 'error' in data:
				raise Exception(data['error']['message'])

			raise Exception('empty-response')



class OpenAIChatTest(BaseLLM):
	def __init__(self, api_key, model='gpt-3.5-turbo', **config):
		self.api_key = api_key
		self.model = model
		self.config = config


	def __call__(self, messages):
		import time
		time.sleep(1)
		return AssistantMessage(text='test')