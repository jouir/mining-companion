import logging

import requests

logger = logging.getLogger(__name__)


def get_rate(ids, vs_currencies):
    logger.debug(f'getting {ids} price in {vs_currencies} on coingecko')
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies={vs_currencies}'
    r = requests.get(url)
    r.raise_for_status()
    logger.debug(r.json())
    return r.json()[ids.lower()][vs_currencies.lower()]
