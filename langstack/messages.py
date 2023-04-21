class SystemMessage:
	def __init__(self, text):
		self.role = 'system'
		self.text = text

class AssistantMessage:
	def __init__(self, text):
		self.role = 'assistant'
		self.text = text

class UserMessage:
	def __init__(self, text):
		self.role = 'user'
		self.text = text