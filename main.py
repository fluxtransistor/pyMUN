import yaml
import pickle
import os
from datetime import datetime

with open("config.yml", "r") as yml_file:
    config = yaml.load(yml_file)


class CommitteeState:
    def __init__(self):
        self.delegations = []
        for country_code in config['committee']['delegations']:
            self.delegations.append(Delegation(country_code))
        self.topic = ''
        self.stage = ''
        self.debate_time = 0


class Delegation:
    def __init__(self, country_code):
        self.country_code = country_code
        speech_time = 0
        poi_time = 0
        poi_answer_time = 0
        motions_raised = 0
        pois_raised = 0
        amendments_made = 0


def save_state():
    state.timestamp = datetime.today()
    try:
        with open("data.pickle", "wb") as f:
            pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as ex:
        print("Error saving committee state:", ex)


def load_state():
    print("Attempting to load a saved committee state...")
    if os.path.isfile("data.pickle"):
        print("No saved state was found, starting from scratch.")
        state = CommitteeState()
    else:
        try:
            with open("data.pickle", "rb") as f:
                global state
                state = pickle.load(f)
                print("Loaded, last saved at " + state.timestamp.strftime('%Y-%m-%d %H:%M:%S'))
        except Exception as ex:
            print("Error loading committee state:", ex)
            quit(1)
