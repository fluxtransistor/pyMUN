import yaml
import pickle
import os
import countrycode
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
        self.country = countrycode.countrycode.countrycode(codes=['country_code'], origin='iso2c',
                                                           target='country_name')
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
    raise Exception("Not implemented.")


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
    print(str(state.num_delegations) + " delegations, 1/2 is " + str(state.half_all) + ", 2/3 are " + str(
        state.two_thirds_all)+".")
    total_time = sum(state.sessions)
    if len(state.sessions) == 1:
        print("There has been 1 session with a duration of "+seconds(total_time))
    if len(state.sessions) > 1:
        print("There have been "+str(len(state.sessions))+" sessions with a total duration of "+seconds(total_time)+".")


print("\nWelcome to pyMUN " + str(VERSION) + "!\n")

state = load_state()
state.begin_session()
sleep(3)
state.end_session()

welcome()

save_state()
