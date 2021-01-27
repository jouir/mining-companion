#!/usr/bin/env python3
import argparse
import logging

from coingecko import get_rate
from config import read_config, validate_config
from requests.exceptions import HTTPError
from state import State

logger = logging.getLogger(__name__)


DEFAULT_STATE_FILE = 'state.json'


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', dest='loglevel', action='store_const', const=logging.INFO,
                        help='print more output')
    parser.add_argument('-d', '--debug', dest='loglevel', action='store_const', const=logging.DEBUG,
                        default=logging.WARNING, help='print even more output')
    parser.add_argument('-o', '--logfile', help='logging file location')
    parser.add_argument('-N', '--disable-notifications', dest='disable_notifications', action='store_true',
                        help='do not send notifications')
    parser.add_argument('-c', '--config', help='configuration file name', default='config.json')
    args = parser.parse_args()
    return args


def setup_logging(args):
    log_format = '%(asctime)s %(levelname)s: %(message)s' if args.logfile else '%(levelname)s: %(message)s'
    logging.basicConfig(format=log_format, level=args.loglevel, filename=args.logfile)


def main():
    args = parse_arguments()
    setup_logging(args)

    config = read_config(args.config)
    validate_config(config)

    state = State(filename=config.get('state_file', DEFAULT_STATE_FILE))

    exchange_rate = None
    currency = config.get('currency')

    notifier = None
    if config.get('telegram') and not args.disable_notifications:
        from telegram import TelegramNotifier
        notifier = TelegramNotifier(**config['telegram'])

    if currency:
        logger.debug('fetching current rate')
        try:
            exchange_rate = get_rate(ids='ethereum', vs_currencies=currency)
        except HTTPError as err:
            logger.warning(f'failed to get ETH/{currency} rate')
            logger.debug(str(err))

    for pool in config.get('pools', []):
        pool_state = state.get(pool)

        if pool == 'flexpool':
            from pools.flexpool import FlexpoolHandler
            handler = FlexpoolHandler(exchange_rate=exchange_rate, currency=currency, notifier=notifier)
        elif pool == 'ethermine':
            from pools.ethermine import EthermineHandler
            handler = EthermineHandler(exchange_rate=exchange_rate, currency=currency, notifier=notifier)
        else:
            logger.warning(f'pool {pool} not supported')
            continue

        last_block = handler.watch_blocks(last_block=pool_state.get('block'))
        if last_block:
            logger.debug(f'saving {pool} block to state file')
            state.write(pool_name=pool, block_number=last_block)

        if config.get('miner'):
            last_balance, last_transaction = handler.watch_miner(address=config['miner'],
                                                                 last_balance=pool_state.get('balance'),
                                                                 last_transaction=pool_state.get('payment'))
            if last_balance:
                logger.debug(f'saving {pool} miner balance to state file')
                state.write(pool_name=pool, miner_balance=last_balance)
            if last_transaction:
                logger.debug(f'saving {pool} miner payment to state file')
                state.write(pool_name=pool, miner_payment=last_transaction)


if __name__ == '__main__':
    main()
