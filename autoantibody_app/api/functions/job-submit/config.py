# Built-in/Generic Imports
import json
import os


class ConfigFactory:
    """
    A class that loads a JSON config file from 
    the ENV_CONFIG environment variable.
    """

    @classmethod
    def get_config(cls):
        # Get the config registered in the system environment.
        # The program assumes that the env variable has been set

        config_file = os.environ['ENV_CONFIG']

        with open(config_file, 'r') as file:
            config = json.load(file)

        return config
