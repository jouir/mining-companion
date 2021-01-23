#!/usr/bin/env python3
import argparse
import logging

import telegram
from coingecko import get_rate
from config import read_config, validate_config
from flexpool import BlockNotFoundException, LastBlock, Miner
from requests.exceptions import HTTPError
from state import read_state, write_state

logger = logging.getLogger(__name__)


DEFAULT_STATE_FILE = 'state.json'
DEFAULT_CURRENCY = 'USD'


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


def watch_block(state_file, config, disable_notifications, exchange_rate=None, currency=None):
    logger.debug('fetching last mined block')
    try:
        block = LastBlock(exchange_rate=exchange_rate, currency=currency)
    except BlockNotFoundException:
        logger.warning('last block found')
        return

    logger.debug('reading state file')
    state = read_state(filename=state_file)

    if block.number != state.get('block'):
        logger.info(f'block {block.number} mined')
        logger.debug(block)

        if not disable_notifications and config.get('telegram'):
            logger.debug('sending block notification to telegram')
            variables = {'number': block.number, 'time': block.time, 'reward': block.reward,
                         'reward_fiat': block.reward_fiat, 'round_time': block.round_time, 'luck': block.luck}
            payload = telegram.create_block_payload(chat_id=config['telegram']['chat_id'], message_variables=variables)
            try:
                telegram.send_message(auth_key=config['telegram']['auth_key'], payload=payload)
                logger.info('block notification sent to telegram')
            except HTTPError as err:
                logger.error('failed to send notification to telegram')
                logger.debug(str(err))

    logger.debug('writing block to state file')
    write_state(filename=state_file, block_number=block.number)


def watch_miner(address, state_file, config, disable_notifications, exchange_rate=None, currency=None):
    logger.debug(f'watching miner {address}')
    try:
        miner = Miner(address=address, exchange_rate=exchange_rate, currency=currency)
    except Exception as err:
        logger.error('failed to find miner')
        logger.debug(str(err))
        return

    logger.debug(miner)

    logger.debug('reading state file')
    state = read_state(filename=state_file)

    # watch balance
    if miner.raw_balance != state.get('balance'):
        logger.info(f'miner {address} balance has changed')
        if not disable_notifications and config.get('telegram'):
            logger.debug('sending balance notification to telegram')
            variables = {'address': address, 'balance': miner.balance, 'balance_fiat': miner.balance_fiat,
                         'balance_percentage': miner.balance_percentage}
            payload = telegram.create_balance_payload(chat_id=config['telegram']['chat_id'],
                                                      message_variables=variables)
            try:
                telegram.send_message(auth_key=config['telegram']['auth_key'], payload=payload)
                logger.info('balance notification sent to telegram')
            except HTTPError as err:
                logger.error('failed to send notification to telegram')
                logger.debug(str(err))

    logger.debug('writing balance to state file')
    write_state(filename=state_file, miner_balance=miner.raw_balance)


def main():
    args = parse_arguments()
    setup_logging(args)

    config = read_config(args.config)
    validate_config(config)
    state_file = config.get('state_file', DEFAULT_STATE_FILE)

    exchange_rate = None
    currency = config.get('currency', DEFAULT_CURRENCY)

    logger.debug('fetching current rate')
    try:
        exchange_rate = get_rate(ids='ethereum', vs_currencies=currency)
    except HTTPError as err:
        logger.warning(f'failed to get ETH/{currency} rate')
        logger.debug(str(err))

    watch_block(state_file, config, args.disable_notifications, exchange_rate, currency)
    watch_miner(config['miner'], state_file, config, args.disable_notifications, exchange_rate, currency)


if __name__ == '__main__':
    main()
