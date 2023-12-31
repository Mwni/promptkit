from copy import deepcopy
from .messages import SystemMessage


class Conversation:
	def __init__(self, messages=[], system_message=None):
		self.messages = messages
		self.system_message = system_message
		
	def append(self, message):
		self.messages.append(message)

	def generate_response(self, llm):
		response = llm(
			messages=self.messages if self.system_message is None else [
				SystemMessage(text=self.system_message),
				*self.messages
			]
		)
		self.messages.append(response)
		return response
	
	def to_plaintext(messages, names={'user': 'User', 'assistant': 'Assistant'}):
		return '%s%s' % (
			'%s\n\n' % messages[0]['text']
			if messages[0]['role'] == 'system'
			else '',
			'\n\n'.join([
				'%s: %s' % (names[m['role'], m['text']])
				for m in messages
			])
		)
	
	def clone(self):
		return deepcopy(self)
	
	def __getitem__(self, index):
		return self.messages[index]
	
	@property
	def last(self):
		return self.messages[-1]