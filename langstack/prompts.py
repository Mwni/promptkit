import os
import yaml
import inspect
from langchain.schema import HumanMessage


class Struct:
	def __init__(self, **entries):
		for k, v in entries.items():
			if isinstance(k, (list, tuple)):
				setattr(self, k, [Struct(**x) if isinstance(x, dict) else x for x in v])
			else:
				setattr(self, k, Struct(**v) if isinstance(v, dict) else v)


def load_yaml(path):
	caller_file = inspect.stack()[1].filename
	caller_dir = os.path.dirname(caller_file)
	path = os.path.join(caller_dir, path)

	with open(path) as f:
		return Struct(**yaml.safe_load(f))


def make_plaintext_transscript(messages):
	return '\n\n'.join([
		('Client: %s' if isinstance(m, HumanMessage) else 'Assistant: %s') % m.content
		for m in messages
	])