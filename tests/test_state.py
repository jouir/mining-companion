import json
import os

import pytest
from companion.state import State


class TestState:
    FILENAME = 'test_state.json'
    POOL_NAME = 'testpool'
    CONTENT = {
        'testpool': {
            'block': 1234,
            'balance': 1234,
            'payment': '0x0000000'
        }
    }

    @pytest.fixture(scope='function')
    def state(self):
        return State(self.FILENAME)

    @pytest.fixture(scope='function')
    def create_state(self):
        with open(self.FILENAME, 'w') as fd:
            json.dump(self.CONTENT, fd, indent=2)
        yield
        if os.path.isfile(self.FILENAME):
            os.unlink(self.FILENAME)

    @pytest.fixture(scope='function')
    def remove_state(self):
        yield
        if os.path.isfile(self.FILENAME):
            os.unlink(self.FILENAME)

    def test_init(self, state, remove_state):
        assert os.path.isfile(self.FILENAME)
        with open(self.FILENAME, 'r') as fd:
            assert json.load(fd) == {}

    def test_read(self, state, create_state):
        content = state.read()
        for pool in self.CONTENT:
            assert pool in content
            for key in self.CONTENT[pool]:
                assert key in content[pool] and content[pool][key] == self.CONTENT[pool][key]

    def test_write(self, state):
        state.write(pool_name=self.POOL_NAME)
        content = state.read()
        assert content[self.POOL_NAME] == {}

    def test_write_block(self, create_state, state):
        state.write(pool_name=self.POOL_NAME, block_number=5678)
        content = state.read()
        assert content[self.POOL_NAME]['block'] == 5678

    def test_write_empty_block(self, create_state, state):
        state.write(pool_name=self.POOL_NAME, block_number=None)
        content = state.read()
        assert content[self.POOL_NAME]['block'] == self.CONTENT[self.POOL_NAME]['block']  # not changed

    def test_write_zero_block(self, create_state, state):
        state.write(pool_name=self.POOL_NAME, block_number=0)
        content = state.read()
        assert content[self.POOL_NAME]['block'] == 0

    def test_write_balance(self, create_state, state):
        state.write(pool_name=self.POOL_NAME, miner_balance=5678)
        content = state.read()
        assert content[self.POOL_NAME]['balance'] == 5678

    def test_write_empty_balance(self, create_state, state):
        state.write(pool_name=self.POOL_NAME, miner_balance=None)
        content = state.read()
        assert content[self.POOL_NAME]['balance'] == self.CONTENT[self.POOL_NAME]['balance']  # not changed

    def test_write_zero_balance(self, create_state, state):
        state.write(pool_name=self.POOL_NAME, miner_balance=0)
        content = state.read()
        assert content[self.POOL_NAME]['balance'] == 0

    def test_write_payment(self, create_state, state):
        state.write(pool_name=self.POOL_NAME, miner_payment='0x1111111')
        content = state.read()
        assert content[self.POOL_NAME]['payment'] == '0x1111111'

    def test_write_empty_payment(self, create_state, state):
        state.write(pool_name=self.POOL_NAME, miner_payment=None)
        content = state.read()
        assert content[self.POOL_NAME]['payment'] == self.CONTENT[self.POOL_NAME]['payment']  # not changed

    def test_get(self, create_state):
        state = State(filename=self.FILENAME)
        assert state.get(self.POOL_NAME) == self.CONTENT[self.POOL_NAME]

    def test_get_missing_key(self, create_state):
        state = State(filename=self.FILENAME)
        assert state.get('UNKNOWN_POOL') == {}
