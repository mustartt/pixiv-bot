import configparser
from typing import Dict

class Credentials:
    def __init__(self, file_loc: str) -> None:
        """Read config file and parse it into a dictionary"""
        conf = configparser.RawConfigParser()
        conf.read(file_loc)
        self.config = conf
        self.file_loc = file_loc

    def get_config(self) -> configparser.RawConfigParser:
        """Returns the config parser"""
        return self.config

    def get_refresh_token(self) -> str:
        """Returns the refreshtoken"""
        return self.config.get('DEFAULT', 'refresh_token')

    def write_refresh_token(self, token: str) -> None:
        """Writes a new refresh_token to config file"""
        self.config.set('DEFAULT', 'refresh_token', token)
        # Writes cfg
        with open(self.file_loc, 'w') as cfg:
            self.config.write(cfg)

    def get_item(self, section: str, name: str) -> str:
        """returns the value under section"""
        return self.config.get(section, name)
