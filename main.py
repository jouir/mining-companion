#!/usr/bin/env python3
import argparse
import logging

import telegram
from coingecko import get_rate
from config import read_config, validate_config
from flexpool import BlockNotFoundException, LastBlock, Miner
from requests.exceptions import HTTPError
from state import create_state, read_state, write_state

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


def watch_block(config, disable_notifications, last_block=None, exchange_rate=None, currency=None):
    logger.debug('fetching last mined block')
    try:
        block = LastBlock(exchange_rate=exchange_rate, currency=currency)
    except BlockNotFoundException:
        logger.warning('last block found')
        return

    if block.number != last_block:
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

    return block


def watch_miner(address, config, disable_notifications, last_balance=None, exchange_rate=None, currency=None):
    logger.debug(f'watching miner {address}')
    try:
        miner = Miner(address=address, exchange_rate=exchange_rate, currency=currency)
    except Exception as err:
        logger.error('failed to find miner')
        logger.debug(str(err))
        return

    logger.debug(miner)

    # watch balance
    if miner.raw_balance != last_balance:
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

    return miner


def main():
    args = parse_arguments()
    setup_logging(args)

    config = read_config(args.config)
    validate_config(config)

    state_file = config.get('state_file', DEFAULT_STATE_FILE)
    create_state(state_file)
    state = read_state(state_file)

    exchange_rate = None
    currency = config.get('currency')

    if currency:
        logger.debug('fetching current rate')
        try:
            exchange_rate = get_rate(ids='ethereum', vs_currencies=currency)
        except HTTPError as err:
            logger.warning(f'failed to get ETH/{currency} rate')
            logger.debug(str(err))

    block = watch_block(last_block=state.get('block'), config=config, disable_notifications=args.disable_notifications,
                        exchange_rate=exchange_rate, currency=currency)
    logger.debug('saving block number to state file')
    write_state(state_file, block_number=block.number)

    miner = watch_miner(last_balance=state.get('balance'), address=config['miner'], config=config,
                        disable_notifications=args.disable_notifications, exchange_rate=exchange_rate,
                        currency=currency)
    logger.debug('saving miner balance to state file')
    write_state(state_file, miner_balance=miner.raw_balance)


if __name__ == '__main__':
    main()
