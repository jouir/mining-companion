import json
import os


def read_state(filename):
    with open(filename, 'r') as fd:
        return json.load(fd)


def write_state(filename, block_number=None, miner_balance=None):
    data = {}
    if os.path.isfile(filename):
        data = read_state(filename)

    if block_number:
        data['block'] = block_number

    if miner_balance:
        data['balance'] = miner_balance

    with open(filename, 'w') as fd:
        json.dump(data, fd)


def create_state(filename):
    if not os.path.isfile(filename):
        write_state(filename)
