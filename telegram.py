import logging
import os
from copy import copy

import requests
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)
absolute_path = os.path.split(os.path.abspath(__file__))[0]


class TelegramNotifier:
    def __init__(self, chat_id, auth_key):
        self._auth_key = auth_key
        self._default_payload = {'auth_key': auth_key, 'chat_id': chat_id, 'parse_mode': 'MarkdownV2',
                                 'disable_web_page_preview': True}

    @staticmethod
    def _markdown_escape(text):
        text = str(text)
        for special_char in ['\\', '`', '*', '_', '{', '}', '[', ']', '(', ')', '#', '+', '-', '.', '!']:
            text = text.replace(special_char, fr'\{special_char}')
        return text

    def _generate_payload(self, message_variables, template_name):
        payload = copy(self._default_payload)
        template_path = os.path.join(absolute_path, 'templates')
        loader = FileSystemLoader(template_path)
        env = Environment(loader=loader)
        template = env.get_template(template_name)
        template_variables = {}
        for key, value in message_variables.items():
            template_variables[key] = self._markdown_escape(value)
        text = template.render(**template_variables)
        payload['text'] = text
        return payload

    def notify_block(self, pool, number, hash, reward, time, round_time, luck, reward_fiat=None):
        message_variables = {'pool': pool, 'number': number, 'hash': hash, 'reward': reward, 'time': time,
                             'round_time': round_time, 'luck': luck, 'reward_fiat': reward_fiat}
        payload = self._generate_payload(message_variables, 'block.md.j2')
        self._send_message(payload)

    def notify_balance(self, pool, address, url, balance, balance_percentage, balance_fiat=None):
        message_variables = {'pool': pool, 'address': address, 'url': url, 'balance': balance,
                             'balance_percentage': balance_percentage, 'balance_fiat': balance_fiat}
        payload = self._generate_payload(message_variables, 'balance.md.j2')
        self._send_message(payload)

    def notify_payment(self, pool, address, txid, amount, time, duration, amount_fiat=None):
        message_variables = {'pool': pool, 'address': address, 'txid': txid, 'amount': amount,
                             'amount_fiat': amount_fiat, 'time': time, 'duration': duration}
        payload = self._generate_payload(message_variables, 'payment.md.j2')
        self._send_message(payload)

    def _send_message(self, payload):
        logger.debug(self._sanitize(payload))
        r = requests.post(f'https://api.telegram.org/bot{self._auth_key}/sendMessage', json=payload)
        r.raise_for_status()

    @staticmethod
    def _sanitize(payload):
        payload = copy(payload)
        if 'auth_key' in payload:
            payload['auth_key'] = '***'
        return payload
