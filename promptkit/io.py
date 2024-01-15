class Inlet:
	def __init__(self):
		self.key = None
		self.awaiting = False
		self.item_event = None
		self.item = None

	def __call__(self, item):
		if self.item:
			raise Exception('cannot set inlet item twice')
		
		self.awaiting = False
		self.item = item
		self.item_event.set()


class Outlet:
	def __init__(self):
		self.key = None
		self.queue = None

	def __call__(self):
		output = []

		while not self.queue.empty():
			output.append(self.queue.get(block=False))

		return output
	
	@property
	def empty(self):
		return self.queue.empty()