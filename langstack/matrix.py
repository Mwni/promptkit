import json


class AgentContainer:
	def create_resumed_agent(self, state):
		agent = self.matrix.get_agent(state['class'])(matrix=self.matrix, **state['attrs'])

		for key, value in state['attrs'].items():
				setattr(agent, key, value)

		agent.resume(state)

		return agent


	def resume(self, state):
		for key, value in state['agents'].items():
			if isinstance(value, list):
				setattr(self, key, [self.create_resumed_agent(state) for state in value])
			else:
				setattr(self, key, self.create_resumed_agent(value))
				



class Matrix(AgentContainer):
	def __init__(self):
		self.agents = []
		self.llms = []
		self.state_handler = None
		self.matrix = self

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
		return {
			'agents': {
				'agent': self.agent.save()
			}
		}

	def resume(self, state):
		super().resume(state)
		self.agent.step()