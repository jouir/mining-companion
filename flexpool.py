import flexpoolapi
from flexpoolapi.utils import format_weis
from humanfriendly import format_timespan


class BlockNotFoundException(Exception):
    pass


def convert_weis(weis, prec=5):
    return round(weis / 10**18, prec)


class LastBlock:
    def __init__(self, exchange_rate=None, currency=None):
        self._exchange_rate = exchange_rate
        self._currency = currency
        block = self.get_last_block()
        self.number = block.number
        self.time = block.time
        self.raw_reward = block.total_rewards
        self.reward = format_weis(block.total_rewards)
        self.reward_fiat = self.convert_reward()
        self.round_time = format_timespan(block.round_time)
        self.luck = f'{int(block.luck*100)}%'

    @staticmethod
    def get_last_block():
        block = flexpoolapi.pool.last_blocks(count=1)[0]
        if not block:
            raise BlockNotFoundException('No block found')
        return block

    def convert_reward(self):
        if self._exchange_rate and self._currency:
            converted = round(convert_weis(self.raw_reward)*self._exchange_rate, 2)
            converted = f'{converted} {self._currency}'
            return converted

    def __repr__(self):
        attributes = {'time': self.time, 'reward': self.reward, 'round_time': self.round_time, 'luck': self.luck}
        if self.reward_fiat:
            attributes['reward_fiat'] = self.reward_fiat
        formatted_attributes = ' '.join([f'{k}="{v}"' for k, v in attributes.items()])
        return f'<Block #{self.number} ({formatted_attributes})>'


class Miner:
    def __init__(self, address, exchange_rate=None, currency=None):
        self.address = address
        self._exchange_rate = exchange_rate
        self._currency = currency
        miner = flexpoolapi.miner(address)
        self.raw_balance = miner.balance()
        self.details = miner.details()
        self.balance = self.format_balance()
        self.balance_fiat = self.convert_balance()
        self.balance_percentage = self.format_balance_percentage()

    def format_balance(self):
        return format_weis(self.raw_balance)

    def format_balance_percentage(self):
        return f'{round(self.raw_balance*100/self.details.min_payout_threshold, 2)}%'

    def convert_balance(self):
        if self._exchange_rate and self._currency:
            converted = round(convert_weis(self.raw_balance)*self._exchange_rate, 2)
            converted = f'{converted} {self._currency}'
            return converted

    def __repr__(self):
        attributes = {'balance': self.balance, 'raw_balance': self.raw_balance,
                      'balance_percentage': self.balance_percentage}
        if self.balance_fiat:
            attributes['balance_fiat'] = self.balance_fiat
        formatted_attributes = ' '.join([f'{k}="{v}"' for k, v in attributes.items()])
        return f'<Miner #{self.address} ({formatted_attributes})>'
