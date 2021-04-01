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
    print(config)


class CommitteeState:
    def __init__(self):
        self.delegations = []
        for country_code in sorted(config['committee']['delegations']):
            self.delegations.append(Delegation(country_code))
        self.num_delegations = len(self.delegations)
        if config['preferences']['other']['majority-plus-one']:
            self.half_all = int(0.5 * self.num_delegations) + 1
            self.two_thirds_all = int((2 / 3) * self.num_delegations) + 1
        else:
            self.half_all = int(0.5 * self.num_delegations)
            self.two_thirds_all = int((2 / 3) * self.num_delegations)
        self.topic = ''
        self.debate = None
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

    def get_half(self):
        if config['preferences']['other']['majority-plus-one']:
            return int(0.5 * self.get_present()) + 1
        else:
            return int(0.5 * self.get_present())

    def get_two_thirds(self):
        if config['preferences']['other']['majority-plus-one']:
            return int((2/3) * self.get_present()) + 1
        else:
            return int((2/3) * self.get_present())

class Delegation:
    def __init__(self, country_code):
        self.country_code = country_code
        self.country = countrycode.countrycode(codes=[country_code], origin='iso2c',
                                                           target='country_name')[0]
        if self.country is None:
            raise Exception("Invalid country code '" + country_code + "'")
        self.veto = country_code in config['committee']['veto']
        self.speech_time = 0
        self.poi_time = 0
        self.poi_answer_time = 0
        self.motions_raised = 0
        self.pois_raised = 0
        self.amendments_made = 0
        self.present = False
        self.no_abstentions = False


class Procedure:
    def __init__(self):
        self.start_time = time()

    def time(self):
        return time() - self.start_time


def seconds(s):
    return str(timedelta(seconds=int(s)))

def save_state():
    state.timestamp = datetime.now()
    if os.path.isfile(FILENAME) and config['preferences']['other']['backup']:
        try:
            copy2(FILENAME,FILENAME+".bkp")
        except Exception as ex:
            print("Error backing up previous committee state:", ex)
    try:
        with open(FILENAME, "wb") as f:
            pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as ex:
        print("Error saving committee state:", ex)


def load_state():
    if not os.path.isfile(FILENAME):
        if not os.path.isfile(FILENAME+".bkp"):
            print("No saved state was found, starting from scratch.\n")
            return CommitteeState()
        else:
            print("Only a backup of the saved state was found, would you like to restore it?")
            if [True, False][decision(["yes","no"],["y","n"])]:
                try:
                    copy2(FILENAME+".bkp", FILENAME)
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
    for delegation in state.delegations:
        print(delegation.country)
        if config['preferences']['roll-call']['present-and-voting']:
            status = decision(['present','absent','present and voting'],['p','a','pv'])
        else:
            status = decision(['present', 'absent'], ['p', 'a'])
        delegation.present = status in [0, 2]
        delegation.no_abstentions = status == 2
    show_quorum()

def show_quorum():
    print(str(state.get_present()) + " delegations present, majority is " + str(state.get_half()) + ", 2/3 majority is " + str(
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
    print("There are "+str(state.num_delegations) + " delegations total, a simple majority is " + str(state.half_all) + ", and a 2/3 majority is " + str(
        state.two_thirds_all)+".")
    total_time = sum(state.sessions)
    sleep(1)
    if len(state.sessions) == 1:
        print("There has been 1 session with a duration of "+seconds(total_time)+".\n")
    if len(state.sessions) > 1:
        print("There have been "+str(len(state.sessions))+" sessions with a total duration of "+seconds(total_time)+".\n")


print("\nWelcome to pyMUN " + str(VERSION) + "!\n")
sleep(0.5)
state = load_state()
sleep(0.5)
welcome()
sleep(1)
state.begin_session()
if state.get_present() == 0:
    print("Let's begin with roll call.\n")
    roll_call()
else:
    print(str(state.get_present())+" delegations are present. Would you like to skip roll call?")
    if [False,True][decision(['skip', 'roll call'], ['s', 'r'])]:
        print("Alright, let's begin with roll call.\n")
        roll_call()

state.end_session()

save_state()
