from time import time
from .messages import SystemMessage, AssistantMessage, UserMessage
from .log import make_logger



class Agent:
	@classmethod
	def from_save_state(cls, assistant, state):
		agent = cls(assistant, start_index=state['start_index'])
		agent.stage = state['stage']

		return agent


	def __init__(self, matrix):
		self.matrix = matrix
		self.transscript = []
		self.request_log = []
		self.stage = 'init'
		self.log = make_logger(self.__class__.__name__)

	def query_llm(self, messages, system_message=None):
		llm = self.matrix.llms[0]

		self.log.info('querying %s' % llm.model)

		if type(messages) == str:
			messages = [UserMessage(text=messages)]

		if system_message:
			messages = [SystemMessage(text=system_message), *messages]

		output = llm(messages=messages)

		self.request_log.append({
			'time': int(time()),
			'input': messages,
			'output': output
		})

		self.log.info('got response of %i chars' % len(output))

		return AssistantMessage(text=output)
		

	def step(self):
		getattr(self, 'reply_%s' % self.stage)()


	def emit_message(self, message):
		self.assistant.assistant_reply(message)


	def get_messages(self, offset=0):
		return self.assistant.chat_history[self.start_index+offset:]


	def get_last_message(self):
		return self.assistant.chat_history[-1]

	def next_stage(self, stage):
		self.stage = stage
		init_func_key = 'enter_%s' % stage

		if hasattr(self, init_func_key):
			getattr(self, init_func_key)()

		
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

	def get_save_state(self):
		return {
			'class': self.__class__.class_id,
			'start_index': self.start_index,
			'stage': self.stage
		}