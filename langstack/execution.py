import os
import threading
import inspect
import time
from .log import make_logger
from .llms.base import BaseLLM
from .messages import message_to_dict, dict_to_message


def execute(fn, journal=None, **kwargs):
	ctx = Context(fn, journal)
	ctx.execute(kwargs)

	return ctx


class Context:
	def __init__(self, fn, journal):
		self.fn = fn
		self.step_event = threading.Event()
		self.step_continue = threading.Event()
		self.result = None
		self.finished = False
		self.journal = Journal(function=fn.__name__, file=inspect.getfile(fn)) if not journal else Journal.from_dict(journal)
		self.log = make_logger('langstack')


	def execute(self, kwargs):
		self.log.info('executing %s' % self.fn.__name__)

		for key, value in kwargs.items():
			if isinstance(value, BaseLLM):
				kwargs[key] = self.wrap_llm(value, key)

		def exec():
			self.result = self.fn(**kwargs)
			self.finished = True
			self.dispatch_step()

		self.thread = threading.Thread(target=exec)
		self.thread.daemon = True
		self.thread.start()


	def step(self):
		self.step_event.wait()
		self.step_continue.set()
		self.step_continue.clear()
		return not self.finished

	
	def dispatch_step(self):
		time.sleep(0.01)
		self.step_event.set()
		self.step_event.clear()
		self.step_continue.wait()


	def wrap_llm(self, llm, key):
		def wrapped_call(messages):
			stack = inspect.stack()[1:]
			result, set_result = self.journal.llm_result(key, stack, messages)
			log = make_logger(find_first_nonlib_call(stack).function)

			if not result:
				log.info('querying %s' % llm.model)
				result = llm(messages)
				log.info('got result of length %i' % len(result.text))
				set_result(result)
			else:
				log.info('replayed %s query with length of %i' % (llm.model, len(result.text)))

			self.dispatch_step()
			return result
		
		return wrapped_call
	


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
	

def find_first_nonlib_call(stack):
	for call in stack:
		if os.path.dirname(__file__) in call.filename:
			continue

		return call