import json
import os


class State:
    def __init__(self, filename):
        self.filename = filename
        self.create()

    def create(self):
        if not os.path.isfile(self.filename):
            with open(self.filename, 'w') as fd:
                json.dump({}, fd)

    def read(self):
        with open(self.filename, 'r') as fd:
            return json.load(fd)

    def write(self, pool_name, block_number=None, miner_balance=None, miner_payment=None):
        content = self.read()
        if pool_name not in content:
            content[pool_name] = {}
        if block_number:
            content[pool_name]['block'] = block_number
        if miner_balance:
            content[pool_name]['balance'] = miner_balance
        if miner_payment:
            content[pool_name]['payment'] = miner_payment
        with open(self.filename, 'w') as fd:
            json.dump(content, fd, indent=2, separators=(',', ': '))

    def get(self, key):
        content = self.read()
        return content.get(key, {})
