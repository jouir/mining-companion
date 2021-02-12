import json
import os

from jsonschema import validate

absolute_path = os.path.split(os.path.abspath(__file__))[0]


class InvalidConfigException(Exception):
    pass


def read_config(filename=None):
    if filename and os.path.isfile(filename):
        with open(filename, 'r') as fd:
            return json.load(fd)
    else:
        return {}


def validate_config(config):
    if config is None:
        raise InvalidConfigException('config is not a dict')
    with open(os.path.join(absolute_path, 'config.schema.json'), 'r') as fd:
        schema = json.loads(fd.read())
        validate(instance=config, schema=schema)
