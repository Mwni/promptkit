import sys
sys.path.append('..')

import os
import json
from argparse import ArgumentParser
from promptkit import execute, Journal, Conversation
from promptkit.io import Inlet, Outlet
from promptkit.llms import OpenAIChat
from promptkit.messages import SystemMessage, UserMessage


parser = ArgumentParser()
parser.add_argument('openai_key', type=str)

args = parser.parse_args()


llm = OpenAIChat(
	api_key=args.openai_key,
	model='gpt-3.5-turbo',
	temperature=0, 
)

journal_path = 'chat.json'

if os.path.exists(journal_path):
	with open(journal_path) as f:
		journal = Journal.from_dict(json.load(f), pop_mismatch=True)
else:
	journal = None


def run_chat(llm, user_input, bot_output):
	conversation = Conversation([
		SystemMessage(text='You are a smug 4chan user who likes to troll the user.'),
		UserMessage(text='Start the conversation by making a short provocative statement to the user (he is a leftie).')
	])

	conversation.generate_response(llm)
	bot_output(conversation.last.text)

	for user_message in user_input:
		conversation.append(UserMessage(text='The soy leftie replied: "%s".\nRespond to this.' % user_message))
		conversation.generate_response(llm)
		bot_output(conversation.last.text)


user_input = Inlet()
bot_output = Outlet()

ctx = execute(
	run_chat,
	journal=journal,
	llm=llm,
	user_input=user_input,
	bot_output=bot_output
)

while not ctx.finished:
	while ctx.step():
		with open(journal_path, 'w') as f:
			json.dump(ctx.journal.to_dict(), f, indent=4)

	print('Bot: %s' % bot_output()[-1])
	user_input(input('You: '))