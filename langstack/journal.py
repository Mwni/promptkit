from .messages import message_to_dict, dict_to_message
from .log import make_logger

log = make_logger('langstack')


class Journal:
	@classmethod
	def from_dict(cls, dict, pop_mismatch=False):
		journal = Journal(function=dict['function'], file=dict['file'])
		journal.cache = dict['cache']
		journal.replay_index = 0
		journal.pop_mismatch = pop_mismatch
		return journal


	def __init__(self, function, file):
		self.function = function
		self.file = file
		self.cache = []
		self.replay_index = None
		self.pop_mismatch = False


	def llm_result(self, key, stack, input):
		stack = self.trim_stack(stack)
		stack = [{'function': call.function, 'file': call.filename} for call in stack]
		input = [message_to_dict(m) for m in input]
		add_to_cache = lambda output: self.cache.append({
			'stack': stack,
			'type': 'llm',
			'key': key,
			'input': input,
			'output': message_to_dict(output)
		})

		if self.replay_index is None or len(self.cache) == 0:
			return None, add_to_cache
		else:
			try:
				cache = self.cache[self.replay_index]

				assert cache['type'] == 'llm', 'wrong type'
				assert cache['key'] == key, 'wrong key'
				assert all(a == b for a, b in zip(stack, cache['stack'])), 'different stack'
				assert all(a == b for a, b in zip(input, cache['input'])), 'different input'
				
			except Exception as e:
				message = 'replay cache mismatch: %s' % str(e)

				if self.pop_mismatch:
					log.warn(message)
					log.info('popping history and continuing fresh from here on')

					self.cache = self.cache[0:self.replay_index]
					self.replay_index = None

					return None, add_to_cache
				else:
					raise Exception(message)
			
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
	