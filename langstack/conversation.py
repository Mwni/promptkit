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