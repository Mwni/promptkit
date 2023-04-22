from time import time
from .matrix import AgentContainer
from .messages import SystemMessage, AssistantMessage, UserMessage
from .log import make_logger



class Agent(AgentContainer):
	@classmethod
	def from_save_state(cls, assistant, state):
		agent = cls(assistant, start_index=state['start_index'])
		agent.stage = state['stage']

		return agent


	def __init__(self, matrix, **inputs):
		self.matrix = matrix
		self.transscript = []
		self.request_log = []
		self.system_message = None
		self.stage = None
		self.stage_entered = False
		self.log = make_logger(self.__class__.__name__)
		


	def step(self):
		if not self.stage_entered:
			self.stage_entered = True
			init_func_key = 'enter_%s' % self.stage if self.stage else 'enter'

			if hasattr(self, init_func_key):
				getattr(self, init_func_key)()

		else:
			getattr(self, 'step_%s' % self.stage if self.stage else 'step')()

		self.matrix.state_change()
		self.step()

		


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


	def spawn_agent(self, name, **inputs):
		agent = self.matrix.get_agent(name)(matrix=self.matrix, **inputs)
		return agent


	def query_llm(self, messages, system_message=None):
		llm = self.matrix.llms[0]

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
			if key in ('matrix', 'log', 'transscript'):
				continue

			if isinstance(value, Agent):
				agents[key] = value.save()
			elif isinstance(value, (tuple, list)) and len(value) > 0 and isinstance(value[0], Agent):
				agents[key] = [agent.save() for agent in value]
			else:
				attrs[key] = value

		return {
			'class': self.__class__.__name__,
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