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


def dict_to_message(dict):
	if dict['role'] == 'system':
		return SystemMessage(text=dict['text'])
	elif dict['role'] == 'assistant':
		return AssistantMessage(text=dict['text'])
	elif dict['role'] == 'user':
		return UserMessage(text=dict['text'])


def invert_roles(messages):
	inverted_messages = []

	for message in messages:
		if message.role == 'assistant':
			inverted_messages.append(UserMessage(text=message.text))
		elif message.role == 'user':
			inverted_messages.append(AssistantMessage(text=message.text))
		else:
			inverted_messages.append(message)

	return inverted_messages