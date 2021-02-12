# mining-companion

Cryptocurrency mining interest has raised recently due to high [Ethereum](https://ethereum.org/en/) profitability. You
can opt for the solo-mining path or use a **mining pool** to increase your chances to receive block rewards.

`mining-companion` is able to listen and notify for the following events:
* new **block** is mined by the mining pool
* unpaid **balance** is updated
* new **payment** has been sent by the mining pool

Notifications are sent via [Telegram Messenger](https://telegram.org/).

## Supported pools

* [Ethermine](https://ethermine.org/)
* [Flexpool.io](https://flexpool.io)

## Installation

```
sudo apt install python3-virtualenv
virtualenv venv
source venv/bin/activate
```

Pool libraries are loaded at execution time. For example, if you use only "flexpool" mining pool, you don't need to
install "ethermine" libraries. Requirements files have been splitted to install only libraries you need.

```
pip install -r requirements/base.txt
pip install -r requirements/ethermine.txt
pip install -r requirements/flexpool.txt
```

To install all libraries at once:

```
pip install -r requirements.txt
```

## Telegram bot

This [tutorial](https://takersplace.de/2019/12/19/telegram-notifications-with-nagios/) explains how to create a Telegram
bot. You'll need the `chat_id` and `auth_key` for the next section.

## Configuration

Configuration file use the JSON format with the following keys:
* `pools`: list of mining pools
* `miner`: wallet address of the miner
* `currency`: symbol of the currency to convert
* `telegram`: send notifications with Telegram
    * `auth_key`: Telegram authentication key for the bot API
    * `chat_id`: Telegram chat room id (where to send the message)
* `state_file`: persist data between runs into this file (default: `state.json`)

See [configuration example](config.example.json).

All options are optional (but the companion would do nothing).

## Usage

```
python3 companion/main.py --help
```


## Contribute

Contributions are welcomed! Feel free to update the code and create a pull-request.

Be sure to lint the code and run tests before:

```
docker build -t pre-commit .
docker run -it -v $(pwd):/mnt/ --rm pre-commit bash
# cd /mnt/
# pip install -r requirements.txt
# pre-commit run --all-files
# pytest
# exit
```
