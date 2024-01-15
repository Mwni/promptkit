import os
import threading
import inspect
import time
from queue import Queue
from .log import make_logger
from .llms.base import BaseLLM
from .io import Inlet, Outlet
from .journal import Journal

log = make_logger('langstack')


def execute(fn, journal=None, **kwargs):
	ctx = Context(fn, journal)
	ctx.execute(kwargs)

	return ctx


class Context:
	def __init__(self, fn, journal):
		self.fn = fn
		self.step_complete = threading.Event()
		self.step_continue = threading.Event()
		self.inlets = []
		self.outlets = []
		self.result = None
		self.finished = False
		self.journal = Journal(function=fn.__name__, file=inspect.getfile(fn)) if not journal else journal


	def execute(self, kwargs):
		log.info('executing %s' % self.fn.__name__)

		for key, value in kwargs.items():
			if isinstance(value, BaseLLM):
				kwargs[key] = self.wrap_llm(value, key)
			elif isinstance(value, Inlet):
				kwargs[key] = self.wrap_inlet(value, key)
			elif isinstance(value, Outlet):
				kwargs[key] = self.wrap_outlet(value, key)

		def exec():
			self.step_continue.wait()
			self.step_continue.clear()
			self.result = self.fn(**kwargs)
			self.finished = True
			self.dispatch_step()

		self.thread = threading.Thread(target=exec)
		self.thread.daemon = True
		self.thread.start()


	def step(self):
		inlets_waiting = [inlet for inlet in self.inlets if inlet.awaiting]

		if len(inlets_waiting) > 0:
			raise Exception('cannot step - inlets awaiting input: %s' % ', '.join([inlet.key for inlet in inlets_waiting]))
		
		self.step_continue.set()
		self.step_complete.wait()
		self.step_complete.clear()
		
		no_inlets_waiting = all([not inlet.awaiting for inlet in self.inlets])

		return not self.finished and no_inlets_waiting

	
	def dispatch_step(self):
		self.step_complete.set()
		self.step_continue.wait()
		self.step_continue.clear()


	def wrap_llm(self, llm, key):
		def wrapped_call(messages):
			stack = inspect.stack()[1:]
			result, set_result = self.journal.advance('llm', key, stack, messages)
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
	

	def wrap_inlet(self, inlet, key):
		inlet.key = key
		inlet.item_event = threading.Event()

		class InletProvider:
			def __init__(self):
				self.made_iter = False

			def __iter__(self):
				if self.made_iter:
					raise Exception('can only call iter on "%s" once' % key)
				
				self.made_iter = True
				return self

			def __next__(_):
				stack = inspect.stack()[1:]
				item, set_item = self.journal.advance('inlet', key, stack)
				log = make_logger(find_first_nonlib_call(stack).function)

				if not item:
					log.info('awaiting inlet item for "%s"' % key)
					inlet.awaiting = True
					self.dispatch_step()
					inlet.item_event.wait()
					inlet.item_event.clear()
					item = inlet.item
					inlet.item = None
					set_item(item)
				else:
					log.info('replayed inlet item for "%s"' % key)

				self.dispatch_step()
				return item
			
		self.inlets.append(inlet)
			
		return InletProvider()


	def wrap_outlet(self, outlet, key):
		outlet.key = key
		outlet.queue = Queue()
		self.outlets.append(outlet)

		def put(item):
			outlet.queue.put(item)

		return put
	


def find_first_nonlib_call(stack):
	for call in stack:
		if os.path.dirname(__file__) in call.filename:
			continue

		return call