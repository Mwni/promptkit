from .messages import message_to_dict, dict_to_message


class Journal:
	@classmethod
	def from_dict(cls, dict):
		journal = Journal(function=dict['function'], file=dict['file'])
		journal.cache = dict['cache']
		journal.replay_index = 0
		return journal


	def __init__(self, function, file):
		self.function = function
		self.file = file
		self.cache = []
		self.replay_index = None


	def llm_result(self, key, stack, input):
		stack = self.trim_stack(stack)
		stack = [{'function': call.function, 'file': call.filename} for call in stack]
		input = [message_to_dict(m) for m in input]

		if self.replay_index is None:
			return None, lambda output: self.cache.append({
				'stack': stack,
				'type': 'llm',
				'key': key,
				'input': input,
				'output': message_to_dict(output)
			})
		else:
			try:
				cache = self.cache[self.replay_index]

				assert cache['type'] == 'llm', 'wrong type'
				assert cache['key'] == key, 'wrong key'
				assert all(a == b for a, b in zip(stack, cache['stack'])), 'different stack'
				assert all(a == b for a, b in zip(input, cache['input'])), 'different input'
				
			except Exception as e:
				raise Exception('replay cache mismatch: %s' % str(e))
			
			self.replay_index += 1

			if self.replay_index >= len(self.cache):
				self.replay_index = None
			
			return dict_to_message(cache['output']), None


	def trim_stack(self, stack):
		for i, call in enumerate(stack):
			if call.function == self.function and call.filename == self.file:
				return stack[0:i]
			
		raise Exception('failed to find stack base')
	

	def to_dict(self):
		return {
			'function': self.function,
			'file': self.file,
			'cache': self.cache
		}
	