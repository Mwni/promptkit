from .messages import message_to_dict, dict_to_message
from .log import make_logger

log = make_logger('langstack')


class Journal:
	@classmethod
	def from_dict(cls, dict, pop_mismatch=False):
		journal = Journal(function=dict['function'], file=dict['file'])
		journal.graph = dict['graph']
		journal.replay_index = 0
		journal.pop_mismatch = pop_mismatch
		return journal


	def __init__(self, function, file):
		self.function = function
		self.file = file
		self.graph = []
		self.replay_index = None
		self.pop_mismatch = False


	def advance(self, type, key, stack, input=None):
		stack = self.trim_stack(stack)
		stack = [{'function': call.function, 'file': call.filename} for call in stack]

		if type == 'llm':
			input = [message_to_dict(m) for m in input]
			read_from_graph = lambda graph: dict_to_message(graph['output'])
			add_to_graph = lambda output: self.graph.append({
				'stack': stack,
				'type': 'llm',
				'key': key,
				'input': input,
				'output': message_to_dict(output)
			})
		else:
			read_from_graph = lambda graph: graph['output']
			add_to_graph = lambda output: self.graph.append({
				'stack': stack,
				'type': type,
				'key': key,
				'input': input,
				'output': output
			})

		if self.replay_index is None or len(self.graph) == 0:
			return None, add_to_graph
		else:
			try:
				graph = self.graph[self.replay_index]

				assert graph['type'] == type, 'wrong type'
				assert graph['key'] == key, 'wrong key'
				assert all(a == b for a, b in zip(stack, graph['stack'])), 'different stack'
				#assert all(a == b for a, b in zip(input, graph['input'])), 'different input'
				
			except Exception as e:
				message = 'replay graph mismatch: %s' % str(e)

				if self.pop_mismatch:
					log.warn(message)
					log.info('popping history and continuing fresh from here on')

					self.graph = self.graph[0:self.replay_index]
					self.replay_index = None

					return None, add_to_graph
				else:
					raise Exception(message)
			
			self.replay_index += 1

			if self.replay_index >= len(self.graph):
				self.replay_index = None
			
			return read_from_graph(graph), None


	def trim_stack(self, stack):
		for i, call in enumerate(stack):
			if call.function == self.function and call.filename == self.file:
				return stack[0:i]
			
		raise Exception('failed to find stack base')
	

	def to_dict(self):
		return {
			'function': self.function,
			'file': self.file,
			'graph': self.graph
		}
	