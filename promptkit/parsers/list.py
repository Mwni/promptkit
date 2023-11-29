import re


def parse_list_simple(text):
	patterns = [
		r"-\s*(.+)",                     # - item 1
		r"\d+\)\s*(.+)",                 # 1) item 1
		r"\d+\.\s*(.+)",                 # 1. item 1
		r"\*\s*(.+)",                    # * item 1
		r"[a-zA-Z]\)\s*(.+)",            # a) item 1
		r"[a-zA-Z]\.\s*(.+)",            # a. item 1
		r"\(\d+\)\s*(.+)",               # (1) item 1
	]

	items = []

	for line in text.splitlines():
		for pattern in patterns:
			match = re.match(pattern, line)
			if match:
				items.append(match.group(1))
				break

	return items