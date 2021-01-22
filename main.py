#!/usr/bin/env python3
import argparse
import logging
import os

import flexpoolapi
import telegram
from coingecko import get_rate
from config import read_config, validate_config
from flexpoolapi.utils import format_weis
from humanfriendly import format_timespan
from requests.exceptions import HTTPError
from state import read_state, write_state

logger = logging.getLogger(__name__)


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


def convert_weis(weis, prec=5):
    return round(weis / 10**18, prec)


def main():
    args = parse_arguments()
    setup_logging(args)

    config = read_config(args.config)
    validate_config(config)
    state_file = config.get('state_file', 'state.json')
    currency = config.get('currency', 'USD')

    logger.debug('fetching last mined block')
    block = flexpoolapi.pool.last_blocks(count=1)[0]

    block_number = block.number
    block_time = block.time
    block_reward = format_weis(block.total_rewards)
    block_round_time = format_timespan(block.round_time)
    block_luck = f'{int(block.luck*100)}%'

    if not block:
        logger.info('no block found')
        return

    if not os.path.isfile(state_file):
        logger.debug('creating state file')
        write_state(filename=state_file, block_number=block.number)
        return

    logger.debug('reading state file')
    state = read_state(filename=state_file)

    if block.number != state['block']:
        logger.info(f'block {block.number} mined')

        logger.debug(f'block time: {block_time}')
        logger.debug(f'block reward: {block_reward}')
        logger.debug(f'block round time: {block_round_time}')
        logger.debug(f'block luck: {block_luck}')

        logger.debug('fetching miner details')

        miner = flexpoolapi.miner(config['miner'])
        miner_balance = miner.balance()
        payout_threshold = miner.details().min_payout_threshold
        balance_percentage = f'{round(miner_balance*100/payout_threshold, 2)}%'

        logger.debug(f'miner unpaid balance: {format_weis(miner_balance)} ({balance_percentage})')

        logger.debug('fetching current rate')
        try:
            rate = get_rate(ids='ethereum', vs_currencies=currency)
        except HTTPError as err:
            logger.error(f'failed to get ETH/{currency} rate')
            logger.debug(str(err))
            return

        balance_converted = round(convert_weis(miner_balance)*rate, 2)
        logger.debug(f'miner unpaid balance converted: {balance_converted} {currency}')

        if not args.disable_notifications and config.get('telegram'):
            logger.debug('sending telegram notification')
            variables = {'block_number': block_number, 'block_time': block_time, 'block_reward': block_reward,
                         'block_round_time': block_round_time, 'block_luck': block_luck,
                         'miner_address': config['miner'], 'miner_balance': format_weis(miner_balance),
                         'miner_balance_converted': balance_converted, 'miner_balance_percentage': balance_percentage,
                         'currency': currency}
            payload = telegram.generate_payload(chat_id=config['telegram']['chat_id'], message_variables=variables)
            try:
                telegram.send_message(auth_key=config['telegram']['auth_key'], payload=payload)
                logger.info('notification sent to telegram')
            except HTTPError as err:
                logger.error('failed to send notification to telegram')
                logger.debug(str(err))

    logger.debug('writing block to state file')
    write_state(filename=state_file, block_number=block.number)


if __name__ == '__main__':
    main()
