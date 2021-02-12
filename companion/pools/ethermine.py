import logging
from datetime import datetime

from ethermine import Ethermine
from humanfriendly import format_timespan
from pools import Handler
from utils import convert_fiat, format_weis

logger = logging.getLogger(__name__)

eth = Ethermine()


class Miner:
    def __init__(self, address, exchange_rate=None, currency=None):
        self.address = address
        self.raw_balance = self.get_unpaid_balance(address)
        self.balance = format_weis(self.raw_balance)
        self.balance_fiat = None
        if exchange_rate and currency:
            self.balance_fiat = convert_fiat(amount=self.raw_balance, exchange_rate=exchange_rate, currency=currency)
        payout_threshold = self.get_payout_threshold(address)
        self.balance_percentage = self.format_balance_percentage(payout_threshold=payout_threshold,
                                                                 balance=self.raw_balance)
        self.transactions = self.get_payouts(address, exchange_rate, currency)

    @staticmethod
    def get_unpaid_balance(address):
        dashboard = eth.miner_dashboard(address)
        return dashboard['currentStatistics']['unpaid']

    @staticmethod
    def get_payouts(address, exchange_rate=None, currency=None):
        payouts = eth.miner_payouts(address)
        # convert to transactions
        transactions = []
        for payout in payouts:
            transaction = Transaction(txid=payout['txHash'], timestamp=payout['paidOn'], amount=payout['amount'],
                                      duration=payout['end']-payout['start'], exchange_rate=exchange_rate,
                                      currency=currency)
            transactions.append(transaction)
        # sort by older timestamp first
        return sorted(transactions)

    @staticmethod
    def get_payout_threshold(address):
        return eth.miner_settings(address)['minPayout']

    @staticmethod
    def format_balance_percentage(payout_threshold, balance):
        return f'{round(balance*100/payout_threshold, 2)}%'

    @property
    def url(self):
        return f'https://ethermine.org/miners/{self.address}/dashboard'

    @property
    def last_transaction(self):
        if self.transactions:
            return self.transactions[-1]

    def __repr__(self):
        attributes = {'balance': self.balance, 'raw_balance': self.raw_balance,
                      'balance_percentage': self.balance_percentage, 'url': self.url}
        if self.balance_fiat:
            attributes['balance_fiat'] = self.balance_fiat
        formatted_attributes = ' '.join([f'{k}="{v}"' for k, v in attributes.items()])
        return f'<Miner #{self.address} ({formatted_attributes})>'


class Transaction:
    def __init__(self, txid, amount, timestamp, duration, exchange_rate=None, currency=None):
        self.txid = txid
        self.time = datetime.fromtimestamp(timestamp)
        self.raw_amount = amount
        self.amount = format_weis(amount)
        self.amount_fiat = None
        self.duration = format_timespan(duration)
        if exchange_rate and currency:
            self.amount_fiat = convert_fiat(amount=self.raw_amount, exchange_rate=exchange_rate, currency=currency)

    def __lt__(self, trx):
        """Order by datetime asc"""
        return self.time < trx.time

    def __eq__(self, trx):
        return self.txid == trx.txid

    def __repr__(self):
        attributes = {'time': self.time, 'amount': self.amount, 'raw_amount': self.raw_amount,
                      'duration': self.duration}
        if self.amount_fiat:
            attributes['amount_fiat'] = self.amount_fiat
        formatted_attributes = ' '.join([f'{k}="{v}"' for k, v in attributes.items()])
        return f'<Transaction #{self.txid} ({formatted_attributes})>'


class EthermineHandler(Handler):
    def __init__(self, exchange_rate=None, currency=None, notifier=None, pool_name='ethermine'):
        super().__init__(pool_name=pool_name, exchange_rate=exchange_rate, currency=currency, notifier=notifier)

    def watch_blocks(self, last_block=None):
        logger.debug('not implemented yet')

    def watch_miner(self, address, last_balance=None, last_transaction=None):
        logger.debug(f'watching miner {address}')
        try:
            miner = Miner(address=address, exchange_rate=self.exchange_rate, currency=self.currency)
        except Exception as err:
            logger.error(f'miner {address} not found')
            logger.exception(err)
            return

        logger.debug(miner)

        last_balance = self._watch_miner_balance(miner=miner, last_balance=last_balance)
        last_transaction = self._watch_miner_payments(miner=miner, last_transaction=last_transaction)

        return last_balance, last_transaction
