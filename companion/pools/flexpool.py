import logging

import flexpoolapi
from humanfriendly import format_timespan
from pools import MAX_NOTIFICATIONS_COUNT, Handler
from utils import convert_fiat, convert_weis, format_weis

logger = logging.getLogger(__name__)

MAX_BLOCKS_COUNT = 10
MAX_PAYMENTS_COUNT = 10


class Block:
    def __init__(self, number, hash, time, round_time, reward, luck, exchange_rate=None, currency=None):
        self.number = int(number)
        self.hash = hash
        self.time = time
        self.round_time = format_timespan(round_time)
        self.reward = format_weis(reward)
        self.reward_fiat = None
        if exchange_rate and currency:
            self.reward_fiat = convert_fiat(amount=reward, exchange_rate=exchange_rate, currency=currency)
        self.luck = f'{int(luck*100)}%'

    def __lt__(self, block):
        return self.number < block.number

    def __repr__(self):
        attributes = {'time': self.time, 'reward': self.reward, 'round_time': self.round_time, 'luck': self.luck}
        if self.reward_fiat:
            attributes['reward_fiat'] = self.reward_fiat
        formatted_attributes = ' '.join([f'{k}="{v}"' for k, v in attributes.items()])
        return f'<Block #{self.number} ({formatted_attributes})>'


class Miner:
    def __init__(self, address, exchange_rate=None, currency=None):
        self.address = address
        miner = flexpoolapi.miner(address)
        self.raw_balance = miner.balance()
        self.balance = convert_weis(self.raw_balance)
        self.balance_fiat = None
        if exchange_rate and currency:
            self.balance_fiat = convert_fiat(amount=self.raw_balance, exchange_rate=exchange_rate, currency=currency)
        payout_threshold = self.get_payout_threshold(miner)
        self.balance_percentage = self.format_balance_percentage(payout_threshold=payout_threshold,
                                                                 balance=self.raw_balance)
        self.transactions = self.get_payements(miner, exchange_rate=exchange_rate, currency=currency)

    @property
    def url(self):
        return f'https://flexpool.io/{self.address}'

    @staticmethod
    def get_payout_threshold(miner):
        return miner.details().min_payout_threshold

    @staticmethod
    def format_balance_percentage(payout_threshold, balance):
        return f'{round(balance*100/payout_threshold, 2)}%'

    @staticmethod
    def get_payements(miner, exchange_rate=None, currency=None):
        # crawl payments
        transactions = []
        payments_count = 0
        current_page = 0
        while payments_count < MAX_PAYMENTS_COUNT:
            logger.debug(f'fetching payments page {current_page}')
            page = miner.payments_paged(page=current_page)
            if not page.contents:
                break
            for payment in page.contents:
                # convert to transaction
                transaction = Transaction(txid=payment.txid, time=payment.time, amount=payment.amount,
                                          duration=payment.duration, exchange_rate=exchange_rate,
                                          currency=currency)
                transactions.append(transaction)
                payments_count += 1
            current_page += 1
            if current_page > page.total_pages:
                break
        # sort transactions from oldest to newest
        return sorted(transactions)

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
    def __init__(self, txid, amount, time, duration, exchange_rate=None, currency=None):
        self.txid = txid
        self.time = time
        self.raw_amount = amount
        self.amount = format_weis(amount)
        self.amount_fiat = None
        self.duration = format_timespan(duration)
        if exchange_rate and currency:
            self.amount_fiat = convert_fiat(amount=self.raw_amount, exchange_rate=exchange_rate, currency=currency)

    def __lt__(self, trx):
        return self.time < trx.time

    def __repr__(self):
        attributes = {'time': self.time, 'amount': self.amount, 'raw_amount': self.raw_amount,
                      'duration': self.duration}
        if self.amount_fiat:
            attributes['amount_fiat'] = self.amount_fiat
        formatted_attributes = ' '.join([f'{k}="{v}"' for k, v in attributes.items()])
        return f'<Transaction #{self.txid} ({formatted_attributes})>'


class FlexpoolHandler(Handler):
    def __init__(self, exchange_rate=None, currency=None, notifier=None, pool_name='flexpool'):
        super().__init__(pool_name=pool_name, exchange_rate=exchange_rate, currency=currency, notifier=notifier)

    def watch_blocks(self, last_block=None):
        logger.debug('watching last blocks')
        last_remote_block = None
        blocks = self.get_blocks(exchange_rate=self.exchange_rate, currency=self.currency)
        if blocks:
            # don't spam block notification at initialization
            for block in blocks[MAX_NOTIFICATIONS_COUNT:]:
                if not last_block or last_block < block.number:
                    logger.info(f'new block {block.number}')
                    if self.notifier:
                        logger.debug('sending block notification')
                        arguments = {'pool': self.pool_name, 'number': block.number, 'hash': block.hash,
                                     'reward': block.reward, 'time': block.time, 'round_time': block.round_time,
                                     'luck': block.luck, 'reward_fiat': block.reward_fiat}
                        try:
                            self.notifier.notify_block(**arguments)
                            logger.info('block notification sent')
                        except Exception as err:
                            logger.error('failed to send notification')
                            logger.exception(err)
            last_remote_block = block
        if last_remote_block and last_remote_block.number:
            return last_remote_block.number

    @staticmethod
    def get_blocks(exchange_rate=None, currency=None):
        remote_blocks = flexpoolapi.pool.last_blocks(count=MAX_BLOCKS_COUNT)
        # convert to blocks
        blocks = []
        for remote_block in remote_blocks:
            block = Block(number=remote_block.number, hash=remote_block.hash, time=remote_block.time,
                          round_time=remote_block.round_time, reward=remote_block.total_rewards, luck=remote_block.luck,
                          exchange_rate=exchange_rate, currency=currency)
            blocks.append(block)
        # sort by block number
        return sorted(blocks)

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
