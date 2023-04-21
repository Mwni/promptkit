

class Matrix:
	def __init__(self):
		self.agents = []
		self.llms = []

	def register_agent(self, cls):
		self.agents.append(cls)

	def register_llm(self, llm):
		self.llms.append(llm)

	def init(self, **inputs):
		self.agent = self.agents[0](**inputs, matrix=self)
		self.agent.entry_init()


	def user_reply(self, text):
		self.chat_history.append(HumanMessage(content=text))
		self.agent.step()

		return self.chat_history[-1] # todo: handle multiple replies


	def assistant_reply(self, message):
		self.chat_history.append(message)
		

	def get_save_state(self):
		return {
			'agent': self.agent.get_save_state() if self.agent else None,
			'chat_history': messages_to_dict(self.chat_history),
			'request_log': self.request_log
		}

	def load_save_state(self, state):
		self.agent = agent_map[state['agent']['class']].from_save_state(self, state['agent'])
		self.chat_history = messages_from_dict(state['chat_history'])
		self.request_log = state['request_log']

	