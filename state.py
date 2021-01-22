import json


def write_state(filename, block_number):
    data = {'block': block_number}
    with open(filename, 'w') as fd:
        json.dump(data, fd)


def read_state(filename):
    with open(filename, 'r') as fd:
        return json.load(fd)
