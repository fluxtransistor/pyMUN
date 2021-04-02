import yaml
import pickle
import os
from countrycode import countrycode
from shutil import copy2
from datetime import datetime, timedelta
from time import time, sleep

VERSION = '0.1.0'
FILENAME = 'committee'

with open("config.yml", "r") as yml_file:
	config = yaml.load(yml_file, Loader=yaml.FullLoader)


class CommitteeState:
	def __init__(self):
		self.delegations = []
		for country_code in sorted(config['committee']['delegations']):
			self.delegations.append(Delegation(country_code))
		self.num_delegations = len(self.delegations)
		if config['preferences']['other']['majority-plus-one']:
			self.half_all = int(0.5 * self.num_delegations) + 1
		else:
			self.half_all = int(0.5 * self.num_delegations)
		self.two_thirds_all = round((2 / 3) * self.num_delegations)
		self.debate = TopicSelection()
		self.topic = None
		self.sessions = []
		self.session_start = 0

	def begin_session(self):
		self.session_start = time()

	def end_session(self):
		if self.session_start == 0:
			raise Exception("Cannot end a session that never began.")
		self.sessions.append(time() - self.session_start)
		self.session_start = 0

	def get_present(self):
		return sum([1 for delegation in self.delegations if delegation.present])

	def get_half(self, num=None):
		if num is None:
			num = self.get_present()
		if config['preferences']['other']['majority-plus-one']:
			return int(0.5 * num) + 1
		else:
			return int(0.5 * num)

	def get_two_thirds(self, num=None):
		if num is None:
			return round((2 / 3) * self.get_present())
		else:
			return round((2 / 3) * num)

	def get_no_abstentions(self):
		return sum([1 for delegation in self.delegations if delegation.no_abstentions])

	def is_veto_present(self):
		return not [1 for delegation in self.delegations if delegation.veto] == []

	def go(self):
		while True:
			try:
				self.debate.go()
			except KeyboardInterrupt:
				print("\nProgram interrupted.")
				if [True, False][decision(['save', "don't save"], ['s', 'n'])]:
					save_state()
					print("Saved successfully.")
				choice = decision(['restart procedure', 'update attendance', 'quit', 'debug'], ['r', 'u', 'q', 'd'])
				if choice == 0:
					continue
				if choice == 1:
					roll_call()
					continue
				if choice == 2:
					self.end_session()
					save_state()
					quit()
				if choice == 3:
					debug()


class Delegation:
	def __init__(self, country_code):
		self.country_code = country_code
		self.country = countrycode.countrycode(codes=[country_code], origin='iso2c', target='country_name')[0]
		if self.country is None:
			raise Exception("Invalid country code '" + country_code + "'")
		self.veto = country_code in config['committee']['veto']
		self.speech_time = 0
		self.poi_time = 0
		self.poi_answer_time = 0
		self.motions_raised = 0
		self.pois_raised = 0
		self.amendments_made = 0
		self.votes = [0, 0, 0]  # keeps track of votes for, against and abstentions
		self.veto_used = 0
		self.present = False
		self.no_abstentions = False


class Procedure:
	subprocedure = None

	def time(self):
		return time() - self.start_time

	def restart_time(self):
		self.start_time = time()

	def go(self):
		self.start_time = time()
		if self.subprocedure is not None:
			return self.subprocedure.go()
		else:
			return self.run_procedure()

	def run_procedure(self):
		pass


class Vote(Procedure):

	def __init__(self, voting_on, vote_type='procedural', majority=None, allow_abstentions=None):
		self.type = vote_type
		self.voting_on = voting_on
		if allow_abstentions is None:
			self.allow_abstentions = config['preferences']['voting'][vote_type]['abstain']
		else:
			self.allow_abstentions = allow_abstentions
		self.allow_veto = config['preferences']['voting'][vote_type]['veto']
		if majority is None:
			self.majority = config['preferences']['voting'][vote_type]['majority']
		else:
			self.majority = majority
		self.chair_vote = config['preferences']['voting'][vote_type]['chair-vote']

	def run_procedure(self):
		if self.chair_vote:
			print(
				"The chair can, by their authority, pass or fail " + self.voting_on + " - or leave it to the committee.")
			choice = decision(['vote', 'pass', 'fail'], ['v', 'p', 'f'])
			if choice == 1:
				return True
			elif choice == 2:
				return False
			print("")
		show_quorum()
		if config['preferences']['voting']['suggest-roll-call']:
			print("Run roll call (attendance) before vote?")
			if [True, False][decision(["yes", "no"], ["y", "n"])]:
				roll_call()
			print("")
		print("The committee is in a voting procedure on " + self.voting_on + ".\n")
		print(
			"For " + self.type + " votes, abstentions are" + ("" if self.allow_abstentions else " not") + " in order.")
		if state.is_veto_present():
			if self.allow_veto:
				print("For delegations with veto powers, voting against will veto " + self.voting_on + ".")
				if self.allow_abstentions:
					print("It's best to abstain.")
			else:
				print("Exercising the veto power is not in order.")
		print("")
		if config['preferences']['voting'][self.type]['default'] == 'headcount':
			result = self.vote_by_headcount()
		else:
			result = self.vote_by_roll_call()
		print("Happy with the vote?")
		choice = decision(["yes", 'override', 'repeat'], ['y', 'o', 'r'])
		if choice == 0:
			return result
		if choice == 1:
			return [True, False][decision(['pass', 'fail'], ['p', 'f'])]
		if choice == 2:
			return self.run_procedure()

	def vote_by_roll_call(self):
		counter = 0
		votes = [0, 0, 0]
		veto = []
		for delegation in state.delegations:
			choices = ['for', 'against', 'abstain']
			keys = ['f', 'a', 'o']
			if not delegation.present:
				print(delegation.country + " is absent.")
				continue
			if delegation.veto and self.allow_veto:
				choices[1] = 'against (VETO)'
			if delegation.no_abstentions and self.allow_abstentions:
				print("Cannot abstain, marked as 'present and voting'.")
			if delegation.no_abstentions or not self.allow_abstentions:
				choices.remove('abstain')
				keys.remove('o')
			if counter == 0:
				choices.append('vote by headcount')
				keys.append('h')
			print(delegation.country)
			vote = decision(choices, keys)
			if vote == 0:
				votes[0] += 1
				delegation.votes[0] += 1
			elif vote == 1:
				votes[1] += 1
				delegation.votes[1] += 1
				if delegation.veto and self.allow_veto:
					veto.append(delegation.country)
					delegation.veto_used += 1
			elif vote == 2 and (not delegation.no_abstentions and self.allow_abstentions):
				votes[2] += 1
				delegation.votes[2] += 1
			else:
				return self.vote_by_headcount()
			counter += 1
		min_votes = state.get_two_thirds(votes[0] + votes[1]) if self.majority == 'two-thirds' else state.get_half(
			votes[0] + votes[1])
		print("\nA majority of " + str(min_votes) + " for is required to pass.")
		print("Result: " + str(votes[0]) + " votes for, " + str(votes[1]) + " votes against, " + str(
			votes[2]) + " abstentions.")
		if veto == [] and votes[0] >= min_votes:
			print("\nThe vote on " + self.voting_on + " thus passes.")
			print("(Clapping might be in order.)")
			return True
		if votes[0] < min_votes:
			print("\nThe vote on " + self.voting_on + " thus fails.")
			return False
		else:
			print("\nThe vote on " + self.voting_on + " fails, as it was vetoed by: " + ', '.join(veto))
			return False

	def vote_by_headcount(self):
		return self.vote_by_roll_call()

	def vote_by_names(self):
		return self.vote_by_roll_call()


# class MultipleChoiceHeadCount(Procedure):
#
# 	def __init__(self, choices, keys, voting_on, type='procedural'):
# 		self.type = type
# 		self.choices = choices
# 		self.keys = keys
# 		self.voting_on = voting_on
# 		self.allow_abstentions = config['preferences']['voting'][type]
#
# 	def run_procedure(self, choices):
# 		print("We are in a voting procedure on " + self.voting_on + ".")
# 		print("Each delegate can choose one of "+len(choices)+)
# 		return 0


def country_input(require_present=True, string=None):
	if string is None:
		string = "Enter the delegation's name: "
	while True:
		output = countrycode.countrycode(codes=[input(string)], origin='country_name', target='iso2c')[0].upper()
		for delegation in state.delegations:
			if delegation.country_code == output:
				if not require_present or delegation.present:
					return state.delegations.index(delegation)
				else:
					print("Delegation is not present.")
					break
		else:
			print("Delegation not found, try the country code?")


def seconds(s):
	return str(timedelta(seconds=int(s)))


def save_state():
	if not config['debug']['do-not-save']:
		state.timestamp = datetime.now()
		if os.path.isfile(FILENAME) and config['preferences']['other']['backup']:
			try:
				copy2(FILENAME, FILENAME + ".bkp")
			except Exception as ex:
				print("Error backing up previous committee state:", ex)
		try:
			with open(FILENAME, "wb") as f:
				pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)
		except Exception as ex:
			print("Error saving committee state:", ex)
	else:
		print("Debug mode - committee not saved.")


def load_state():
	if not os.path.isfile(FILENAME):
		if not os.path.isfile(FILENAME + ".bkp"):
			print("No saved state was found, starting from scratch.\n")
			return CommitteeState()
		else:
			print("Only a backup of the saved state was found, would you like to restore it?")
			if [True, False][decision(["yes", "no"], ["y", "n"])]:
				try:
					copy2(FILENAME + ".bkp", FILENAME)
				except Exception as ex:
					print("Error restoring the backup:", ex)
				return load_state()
			print("Starting from scratch.")
			return CommitteeState()

	else:
		try:
			with open(FILENAME, "rb") as f:
				pickle_state = pickle.load(f)
				print("The committee was last saved at " + pickle_state.timestamp.strftime('%Y-%m-%d %H:%M:%S') + ".\n")
				return pickle_state
		except Exception as ex:
			print("Error loading committee state:", ex)
			quit(2)


def roll_call():
	all_present = False
	if config['preferences']['roll-call']['all-present']:
		print("Would you like to mark all delegates as present?")
		all_present = [True, False][decision(['yes', 'no'], ['y', 'n'])]
		if not all_present:
			print("OK. Let's do it one by one then.")
	if all_present:
		if config['preferences']['roll-call']['present-and-voting'] and state.get_no_abstentions() > 0:
			print("How would you like to mark delegates that were previously 'present and voting'?")
			keep_no_abstentions = [False, True][decision(['present', 'present and voting'], ['p', 'pv'])]
		else:
			keep_no_abstentions = False
		for delegation in state.delegations:
			delegation.present = True
			delegation.no_abstentions = keep_no_abstentions and delegation.no_abstentions
	else:
		for delegation in state.delegations:
			print(delegation.country)
			if config['preferences']['roll-call']['present-and-voting']:
				status = decision(['present', 'absent', 'present and voting'], ['p', 'a', 'pv'])
			else:
				status = decision(['present', 'absent'], ['p', 'a'])
			delegation.present = status in [0, 2]
			delegation.no_abstentions = status == 2
	show_quorum()


def show_quorum():
	print(str(state.get_present()) + " delegations present, majority is " + str(
		state.get_half()) + ", 2/3 majority is " + str(
		state.get_two_thirds()) + ".")


def decision(options, keys):
	keys = [i.lower() for i in keys]
	print("Type " + ' / '.join(["'" + keys[i] + "' = " + options[i] for i in range(len(keys))]))
	options = [i.lower() for i in options]
	while True:
		choice = input().lower()
		if choice in keys:
			return keys.index(choice)
		if choice in options:
			return options.index(choice)
		else:
			print("Sorry, please try again?")


def welcome():
	print("Welcome to the " + config['committee']['name'] + " in " + config['committee']['conference'] + "!")
	sleep(1)
	print("There are " + str(state.num_delegations) + " delegations total, a simple majority is " + str(
		state.half_all) + ", and a 2/3 majority is " + str(
		state.two_thirds_all) + ".")
	total_time = sum(state.sessions)
	sleep(1)
	if len(state.sessions) == 1:
		print("There has been 1 session with a duration of " + seconds(total_time) + ".\n")
	if len(state.sessions) > 1:
		print("There have been " + str(len(state.sessions)) + " sessions with a total duration of " + seconds(
			total_time) + ".\n")


class Resolution(Procedure):
	pass


class TopicSelection(Procedure):

	def run_procedure(self):
		if len(config['committee']['topics']) == 0:
			state.topic = input("Please enter the topic: ")
		else:
			print("\nLet's select a committee topic. How would you like to pick one?")
			if len(config['committee']['topics']) > 1:
				choice = decision(['vote', 'choose', 'enter manually'], ['v', 'c', 'm'])
				if choice == 0:
					vote = Vote("Topic 1", 'procedural')
					state.topic = config['committee']['topics'][0 if vote.go() else 1]
				if choice == 1:
					n_topics = len(config['committee']['topics'])
					for i in range(n_topics):
						print(str(i + 1) + ") " + config['committee']['topics'][i])
					topic_choice = decision(["topic " + str(x + 1) for x in range(n_topics)],
											[str(x + 1) for x in range(n_topics)])
					state.topic = config['committee']['topics'][topic_choice]
				if choice == 2:
					state.topic = input("Please enter the topic: ")
			else:
				if [False, True][decision(['use configured topic', 'enter manually'], ['u', 'm'])]:
					state.topic = input("Please enter the topic: ")
				else:
					state.topic = config['committee']['topics'][0]
		print("The committee topic is now " + state.topic + ".")
		state.debate = MotionSelector()


class MotionSelector(Procedure):

	def run_procedure(self):
		possible_motions = ['unmod caucus', 'mod caucus']
		keys = ['u', 'm']
		if self == state.debate:
			possible_motions.append('introduce reso')
			keys.append('r')
		if type(state.debate) == Resolution() and self == state.debate.subprocedure:
			possible_motions.append('introduce amendment')
			keys.append('a')
			possible_motions.append('move to closed debate')
			keys.append('c')
		possible_motions.append('adjourn session')
		keys.append('q')
		motions = []
		raised_by = "no one"
		while True:
			print("Motions may now be proposed.")
			if len(motions) == 0:
				choice = decision(["delegate motion", "chair motion", "quit"], ["d", "c", "q"])
				if choice == 2:
					raise KeyboardInterrupt()
			else:
				choice = decision(["delegate motion", "chair motion", "no more motions"], ["d", "c", "n"])
			if choice == 0:
				delegate = country_input()
				state.delegations[delegate].motions_raised += 1
				raised_by = state.delegations[delegate].country
				motions.append(possible_motions[decision(possible_motions, keys)])
			if choice == 1:
				motions.append(possible_motions[decision(possible_motions, keys)])
			if choice == 2:
				break
		if len(motions) > 0:
			print("Motion to " + motions[0] + " by " + raised_by + ".")


class Motion():
	pass


def debug():
	print("Debugger not implemented. Sorry!")
	# TODO: implement debugger
	decision(["continue"], ['c'])


if __name__ == '__main__':
	print("\nWelcome to pyMUN " + str(VERSION) + "!\n")
	sleep(0.5)
	state = load_state()
	sleep(0.5)
	welcome()
	sleep(1)
	state.begin_session()
	if state.get_present() == 0:
		print("\nLet's begin with roll call.\n")
		sleep(1)
		roll_call()
	else:
		print(str(state.get_present()) + " delegations were previously present. Would you like to skip roll call?")
		if [False, True][decision(['skip', 'roll call'], ['s', 'r'])]:
			print("Alright, let's begin with roll call.\n")
			roll_call()

	state.go()
	state.end_session()

	save_state()
