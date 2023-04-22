

class AgentContainer:
	def save(self):
		return {
			'agent': self.agent.get_save_state() if self.agent else None,
			'chat_history': messages_to_dict(self.chat_history),
			'request_log': self.request_log
		}

	def resume(self, state):
		self.agent = agent_map[state['agent']['class']].from_save_state(self, state['agent'])
		self.chat_history = messages_from_dict(state['chat_history'])
		self.request_log = state['request_log']


class Matrix(AgentContainer):
	def __init__(self):
		self.agents = []
		self.llms = []
		self.state_handler = None

	def register_agent(self, cls):
		self.agents.append(cls)

	def register_llm(self, llm):
		self.llms.append(llm)

	def register_state_handler(self, handler):
		self.state_handler = handler

	def init(self, **inputs):
		self.agent = self.agents[0](**inputs, matrix=self)
		self.agent.step()

	def get_agent(self, name):
		return next(agent for agent in self.agents if agent.__name__ == name)

	def state_change(self):
		if self.state_handler:
			self.state_handler()

	def save(self):
		pass