import re


def parse_choice_simple(text):
	match = re.match(r'\s?.*?(?:([0-9]+)|([a-zA-Z]))([ \,\.\:\;\#\)]|$)', text)

	if not match:
		return None
	
	if match.group(1):
		return int(match.group(1)) - 1

	if match.group(2):
		return ord(match.group(2).lower()) - 97