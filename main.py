import yaml
import pickle
import os
import countrycode
from datetime import datetime
from time import time

VERSION = '0.1.0'
state = None


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
            self.half = int(0.5 * self.num_delegations) + 1
            self.two_thirds = int((2/3) * self.num_delegations) + 1
        else:
            self.half = int(0.5 * self.num_delegations)
            self.two_thirds = int((2 / 3) * self.num_delegations)
        self.topic = ''
        self.debate = None
        self.debate_time = 0


class Delegation:
    def __init__(self, country_code):
        self.country_code = country_code
        self.country = countrycode.countrycode.countrycode(codes=['country_code'],origin='iso2c',target='country_name')
        if self.country is None:
            raise Exception("Invalid country code '"+country_code+"'")
            quit(3)
        veto = country_code in config['committee']['veto']
        speech_time = 0
        poi_time = 0
        poi_answer_time = 0
        motions_raised = 0
        pois_raised = 0
        amendments_made = 0


class Procedure:
    def __init__(self):
        self.start_time=time()

    def time(self):
        return time() - self.start_time


def save_state():
    state.timestamp = datetime.now()
    try:
        with open("data.pickle", "wb") as f:
            pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as ex:
        print("Error saving committee state:", ex)


def load_state():
    if not os.path.isfile("data.pickle"):
        print("No saved state was found, starting from scratch.\n")
        return CommitteeState()
    else:
        try:
            with open("data.pickle", "rb") as f:
                state = pickle.load(f)
                print("The committee was last saved at " + state.timestamp.strftime('%Y-%m-%d %H:%M:%S')+".\n")
                return state
        except Exception as ex:
            print("Error loading committee state:", ex)
            quit(2)


def roll_call():
    raise Exception("Not implemented.")
    quit(100)


def welcome():
    print("Welcome to the "+config['committee']['name']+" in "+config['committee']['conference']+"!")
    print(str(state.num_delegations)+" countries, 1/2 is "+str(state.half)+", 2/3 are "+str(state.two_thirds))


print("\nWelcome to pyMUN "+str(VERSION)+"!\n")
session_start = time()
state = load_state()
welcome()
save_state()
