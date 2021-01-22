import logging
import os

import requests
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)
absolute_path = os.path.split(os.path.abspath(__file__))[0]


def markdown_escape(text):
    text = str(text)
    for special_char in ['\\', '`', '*', '_', '{', '}', '[', ']', '(', ')', '#', '+', '-', '.', '!']:
        text = text.replace(special_char, fr'\{special_char}')
    return text


def generate_payload(chat_id, message_variables, template_file_name=None):
    payload = {'chat_id': chat_id, 'parse_mode': 'MarkdownV2'}
    if not template_file_name:
        template_file_name = os.path.join(absolute_path, 'message.md.j2')
    template_path = os.path.dirname(os.path.abspath(template_file_name))
    template_name = os.path.basename(os.path.abspath(template_file_name))
    loader = FileSystemLoader(template_path)
    env = Environment(loader=loader)
    template = env.get_template(template_name)
    template_variables = {}
    for key, value in message_variables.items():
        template_variables[key] = markdown_escape(value)
    text = template.render(**template_variables)
    payload['text'] = text
    return payload


def send_message(auth_key, payload):
    logger.debug(payload)
    r = requests.post(f'https://api.telegram.org/bot{auth_key}/sendMessage', json=payload)
    r.raise_for_status()
