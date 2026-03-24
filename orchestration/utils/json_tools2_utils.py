"""JSON tools2 utilities"""

import json


def json_dump(obj, fp):
    """JSON dump to file"""
    json.dump(obj, fp)


def json_load(fp):
    """JSON load from file"""
    return json.load(fp)
