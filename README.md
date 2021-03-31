# pyMUN
 A simple yet nimble CLI interface for MUN chairing.

## Prerequisites
pyMUN runs in Python 3, as suggested by the name. Install the packages in `requirements.txt` into your python venv of choice. 

If you wish to install them globally, `cd` into the folder and run `pip3 install -r requirements.txt`

## Configuration
The `config.yml.default` file provides an example configuration.

Run `cp config.yml.default config.yml` and modify the config to your liking. The setup should be quite self-explanatory, but contributions to help create proper documentation are very welcome.

## Running
Run `main.py` in your venv, or just `python3 main.py`.

The program saves a pickle of the current committee state in the `committee` file. Optionally, an existing `committee` file can be backed up to `committee.bkp` before it is overwritten, providing a snapshot of the previous save.


