import os
import threading
import inspect
import time
from .log import make_logger
from .llms.base import BaseLLM
from .journal import Journal

log = make_logger('langstack')


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
		self.journal = Journal(function=fn.__name__, file=inspect.getfile(fn)) if not journal else journal


	def execute(self, kwargs):
		log.info('executing %s' % self.fn.__name__)

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
	

def find_first_nonlib_call(stack):
	for call in stack:
		if os.path.dirname(__file__) in call.filename:
			continue

		return call