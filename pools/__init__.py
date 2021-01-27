import logging

logger = logging.getLogger(__name__)

MAX_NOTIFICATIONS_COUNT = 5


class Handler:
    def __init__(self, pool_name, exchange_rate=None, currency=None, notifier=None):
        self.pool_name = pool_name
        self.exchange_rate = exchange_rate
        self.currency = currency
        self.notifier = notifier

    def _watch_miner_balance(self, miner, last_balance=None):
        logger.debug('watching miner balance')
        if miner.raw_balance != last_balance:
            logger.info('miner balance has changed')
            if self.notifier:
                logger.debug('sending balance notification')
                arguments = {'pool': self.pool_name, 'address': miner.address, 'url': miner.url,
                             'balance': miner.balance, 'balance_fiat': miner.balance_fiat,
                             'balance_percentage': miner.balance_percentage}
                try:
                    self.notifier.notify_balance(**arguments)
                    logger.info('balance notification sent')
                except Exception as err:
                    logger.error('failed to send notification')
                    logger.exception(err)
        return miner.raw_balance

    def _watch_miner_payments(self, miner, last_transaction=None):
        if miner.last_transaction and miner.last_transaction.txid != last_transaction:
            logger.debug('watching miner payments')
            # send notifications for recent payements only
            for transaction in miner.transactions[MAX_NOTIFICATIONS_COUNT:]:
                if not last_transaction or transaction.txid > last_transaction:
                    logger.info(f'new payment {transaction.txid}')
                    if self.notifier:
                        logger.debug('sending payment notification')
                        arguments = {'pool': self.pool_name, 'address': miner.address, 'txid': transaction.txid,
                                     'amount': transaction.amount, 'amount_fiat': transaction.amount_fiat,
                                     'time': transaction.time, 'duration': transaction.duration}
                        try:
                            self.notifier.notify_payment(**arguments)
                            logger.info('payment notification sent')
                        except Exception as err:
                            logger.error('failed to send notification')
                            logger.exception(err)
        if miner.last_transaction and miner.last_transaction.txid:
            return miner.last_transaction.txid
