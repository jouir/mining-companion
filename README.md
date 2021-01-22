# flexpool-activity

[Flexpool.io](https://flexpool.io) is a next-generation [Ethereum](https://ethereum.org/en/) mining pool known for their
[#STOPEIP1559](https://stopeip1559.org/) move. `flexpool-activity` is able to listen and notify when a new **block** is
mined by the pool and display the up-to-date **miner balance** and convert it to **fiat**.

## Installation

```
sudo apt install python3-virtualenv
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Telegram bot

This [tutorial](https://takersplace.de/2019/12/19/telegram-notifications-with-nagios/) explains how to create a Telegram
bot. You'll need the `chat_id` and `auth_key` for the next section.

## Configuration

Configuration file use the JSON format with the following keys:
* `miner`: wallet address of the miner
* `currency`: symbol of the currency to convert (default: USD)
* `telegram`: send notifications with Telegram (optional)
    * `auth_key`: Telegram authentication key for the bot API
    * `chat_id`: Telegram chat room id (where to send the message)
* `state_file`: persist data between runs into this file (default: `state.json`)

See [configuration example](config.example.json).


## Usage

```
python3 main --help
```


## Contribute

Contributions are welcomed! Feel free to update the code and create a pull-request.

Be sure to lint the code before:

```
docker build -t pre-commit .
docker run -it -v $(pwd):/mnt/ --rm pre-commit bash
# cd /mnt/
# pre-commit run --all-files
# exit
```
