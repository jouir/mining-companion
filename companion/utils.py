def convert_weis(weis, precision=5):
    return round(weis / 10**18, precision)


def format_weis(weis, precision=5):
    amount = convert_weis(weis=weis, precision=precision)
    if amount == int(amount):
        amount = int(amount)
    return f'{amount} ETH'


def convert_fiat(amount, exchange_rate, currency):
    converted = round(convert_weis(amount)*exchange_rate, 2)
    converted = f'{converted} {currency}'
    return converted
