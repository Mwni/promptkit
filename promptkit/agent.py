import os
import inspect
from importlib import import_module, util as import_util
from time import time
from .messages import SystemMessage, AssistantMessage, UserMessage 
from .messages import dict_to_message
from .log import make_logger



class Agent:
	@staticmethod
	def load_agent(file, cls):
		spec = import_util.spec_from_file_location('agents.%s' % os.path.basename(file)[0:-3], file)
		module = import_util.module_from_spec(spec)
		spec.loader.exec_module(module)
		return getattr(module, cls)

	@classmethod
	def resume(cls, state, parent=None):
		agent = cls(parent=parent, **state['attrs'])
		agent.transscript = [dict_to_message(m) for m in state['transscript']]

		for key, value in state['attrs'].items():
				setattr(agent, key, value)

		for key, value in state['agents'].items():
			if isinstance(value, list):
				setattr(agent, key, [cls.load_agent(state['file'], state['class']).resume(state, agent) for state in value])
			else:
				setattr(agent, key, cls.load_agent(value['file'], value['class']).resume(value, agent))

		return agent


	

	def __init__(self, parent=None, **inputs):
		self.parent = parent
		self.transscript = []
		self.llms = []
		self.request_log = []
		self.system_message = None
		self.stage = None
		self.stage_entered = False
		self.running_agents = None
		self.terminated = False
		self.log = make_logger(self.__class__.__name__)


	def step(self):
		if self.terminated:
			return
		
		if self.running_agents:
			all_done = True

			for i, agent in enumerate(self.running_agents):
				if not agent.final_result:
					agent.step()
					all_done = False

			



		if not self.stage_entered:
			self.stage_entered = True

			init_func_key = 'enter_%s' % self.stage if self.stage else 'enter'

			if hasattr(self, init_func_key):
				getattr(self, init_func_key)()
		else:
			getattr(self, 'step_%s' % self.stage if self.stage else 'step')()

		
	def use_llm(self, llm):
		self.llms.append(llm)

	def run_agents(self, agents):
		self.running_agents = [agents]


	def set_system_message(self, message):
		self.system_message = message


	def emit_message(self, message):
		if type(message) == str:
			message = AssistantMessage(text=message)

		self.transscript.append(message)


	def user_reply(self, message):
		message = UserMessage(text=message if type(message) == str else message.text)
		self.transscript.append(message)


	def generate_response(self):
		response = self.query_llm(
			messages=self.transscript, 
			system_message=self.system_message
		)
		self.transscript.append(response)


	def next_stage(self, stage):
		self.stage = stage
		self.stage_entered = False


	def terminate(self):
		self.terminated = True


	def query_llm(self, messages, system_message=None):
		if len(self.llms) > 0:
			llms = self.llms
		else:
			parent = self.parent

			while parent:
				if len(parent.llms) > 0:
					llms = parent.llms
					break

				parent = parent.parent

		llm = llms[0]

		self.log.info('querying %s' % llm.model)

		if type(messages) == str:
			messages = [UserMessage(text=messages)]

		if system_message:
			messages = [SystemMessage(text=system_message), *messages]

		messages = [{'role': m.role, 'content': m.text} for m in messages]
		output = llm(messages=messages)

		self.request_log.append({
			'time': int(time()),
			'input': messages,
			'output': output
		})

		self.log.info('got response of %i chars' % len(output))

		return AssistantMessage(text=output)


	def save(self):
		agents = {}
		attrs = {}

		for key, value in vars(self).items():
			if key in ('parent', 'llms', 'log', 'transscript'):
				continue

			if hasattr(self, 'save_skip') and key in self.save_skip:
				continue

			if isinstance(value, Agent):
				agents[key] = value.save()
			elif isinstance(value, (tuple, list)) and len(value) > 0 and isinstance(value[0], Agent):
				agents[key] = [agent.save() for agent in value]
			else:
				attrs[key] = value

		return {
			'class': self.__class__.__name__,
			'file': inspect.getfile(self.__class__),
			'transscript': [m.__dict__ for m in self.transscript],
			'agents': agents,
			'attrs': attrs,
		}

	

	'''
	def generate_chat(self, system_message, chat_history):
		return self.assistant.query_chat_model(
			[
				SystemMessage(content=system_message),
				*chat_history
			], 
			brain_tier=2
		)

	def generate_response(self, system_message, instruction, **inputs):
		return self.assistant.query_chat_model(
			[
				SystemMessage(content=system_message),
				HumanMessage(content=instruction.format(**inputs))
			], 
			brain_tier=2
		)

	def determine_case(self, cases, **input):
		self.log.info('determine one of cases: %s' % (', '.join(cases.keys())))

		for key, case in cases.items():
			parser = BooleanOutputParser(
				context=case['context'],
				question=case['question']
			)

			output = self.assistant.query_chat_model(
				[
					SystemMessage(
						content=case['system_message']
					),
					HumanMessage(
						content=parser
							.create_prompt_template()
							.format(**input)
					)
				], 
				brain_tier=2
			)

			result = parser.parse(output)

			self.log.info('case %s: %s' % (key, str(result)))

			if result == True:
				return key


	def determine_choice(self, system_message, options, user_input, **extra):
		parser = SimpleChoiceOutputParser([
			OutputOption(name, description) 
			for name, description in options.items()
		])

		output = self.assistant.query_chat_model(
			[
				SystemMessage(
					content=system_message
				),
				HumanMessage(
					content=parser
						.create_prompt_template()
						.format(input=user_input.content)
				)
			], 
			brain_tier=2
		)

		return parser.parse(output)

	'''