import yaml
import pickle
import os
import countrycode
from datetime import datetime


state = None


with open("config.yml", "r") as yml_file:
    config = yaml.load(yml_file, Loader=yaml.FullLoader)
    print(config)


class CommitteeState:
    def __init__(self):
        self.delegations = []
        for country_code in sorted(config['committee']['delegations']):
            self.delegations.append(Delegation(country_code))
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
        speech_time = 0
        poi_time = 0
        poi_answer_time = 0
        motions_raised = 0
        pois_raised = 0
        amendments_made = 0


class Procedure:
    def __init__(self):
        self.start_time=datetime.now()

    def time(self):
        return datetime.today() - self.start_time


def save_state():
    state.timestamp = datetime.now()
    try:
        with open("data.pickle", "wb") as f:
            pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as ex:
        print("Error saving committee state:", ex)


def load_state():
    print("Attempting to load a saved committee state...")
    if not os.path.isfile("data.pickle"):
        print("No saved state was found, starting from scratch.")
        return CommitteeState()
    else:
        try:
            with open("data.pickle", "rb") as f:
                state = pickle.load(f)
                print("Loaded, last saved at " + state.timestamp.strftime('%Y-%m-%d %H:%M:%S'))
                return state
        except Exception as ex:
            print("Error loading committee state:", ex)
            quit(2)


def roll_call():
    raise Exception()


session_start = datetime.now()
state = load_state()
save_state()
