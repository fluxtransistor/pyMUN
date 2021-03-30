import yaml
import pickle

with open("config.yml", "r") as yml_file:
    config = yaml.load(yml_file)

state = None


def save_state():
    try:
        with open("data.pickle", "wb") as f:
            pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as ex:
        print("Error saving committee state:", ex)
