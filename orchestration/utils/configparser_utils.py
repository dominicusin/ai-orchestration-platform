"""ConfigParser utilities"""

import configparser
from typing import Dict


def parse_ini(path: str) -> configparser.ConfigParser:
    """Parse INI file"""
    config = configparser.ConfigParser()
    config.read(path)
    return config


def ini_to_dict(config: configparser.ConfigParser) -> Dict:
    """Convert INI to dict"""
    return {section: dict(config[section]) for section in config.sections()}


def write_ini(path: str, data: Dict):
    """Write INI file"""
    config = configparser.ConfigParser()
    for section, values in data.items():
        config[section] = values
    with open(path, 'w') as f:
        config.write(f)


def get_ini_value(config: configparser.ConfigParser, section: str, key: str, fallback: str = None) -> str:
    """Get INI value"""
    return config.get(section, key, fallback=fallback)
