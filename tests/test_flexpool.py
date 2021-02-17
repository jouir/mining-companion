from datetime import datetime, timedelta

import pytest
from companion.pools.flexpool import FlexpoolHandler, Transaction
from flexpoolapi.shared import Block as BlockApi


class TestFlexpoolHandler:
    def test_init(self):
        handler = FlexpoolHandler()
        assert handler.pool_name == 'flexpool'

    @pytest.mark.parametrize(
        'old_balance,new_balance,should_notify',
        [
            pytest.param(1, 2, True, id='new_balance_with_notification'),
            pytest.param(1, 0, True, id='new_balance_after_payment_with_notification'),
            pytest.param(None, 1, True, id='very_new_balance_with_notification'),
            pytest.param(1, 1, False, id='same_balance_without_notification'),
        ]
    )
    def test_balance(self, mocker, old_balance, new_balance, should_notify):
        notifier = mocker.Mock()
        notifier.notify_balance = mocker.Mock()
        handler = FlexpoolHandler(notifier=notifier)
        miner = mocker.patch('flexpoolapi.miner')
        miner().balance.return_value = new_balance
        mocker.patch('companion.pools.flexpool.FlexpoolHandler._watch_miner_payments')
        mocker.patch('companion.pools.flexpool.Miner.get_payements')
        last_balance, last_transaction = handler.watch_miner(address='addr', last_balance=old_balance)
        assert last_balance == new_balance
        if should_notify:
            notifier.notify_balance.assert_called_once()
        else:
            notifier.notify_balance.assert_not_called()

    def test_balance_with_api_failure(self, mocker):
        """An API failure should not send a balance notification"""
        notifier = mocker.Mock()
        notifier.notify_balance = mocker.Mock()
        handler = FlexpoolHandler(notifier=notifier)
        request_get = mocker.patch('requests.get')
        request_get.return_value.status_code = 503
        mocker.patch('companion.pools.flexpool.FlexpoolHandler._watch_miner_payments')
        mocker.patch('companion.pools.flexpool.Miner.get_payements')
        last_balance, last_transaction = handler.watch_miner(address='0000000000000000000000000000000000000001',
                                                             last_balance=1)
        assert last_balance is None
        notifier.notify_balance.assert_not_called()

    @staticmethod
    def _create_transactions(names):
        if names:
            return [Transaction(txid=n, amount=1, time=datetime.now(), duration=timedelta(minutes=1)) for n in names]

    @pytest.mark.parametrize(
        'old_transaction,new_transactions,should_notify',
        [
            pytest.param('trx1', ['trx1', 'trx2'], True, id='new_payment_with_notification'),
            pytest.param(None, ['trx1'], True, id='very_new_payment_with_notification'),
            pytest.param('trx1', ['trx1'], False, id='same_payment_without_notification'),
            pytest.param(None, None, False, id='zero_payment_without_notification'),
        ]
    )
    def test_payments(self, mocker, old_transaction, new_transactions, should_notify):
        notifier = mocker.Mock()
        notifier.notify_payment = mocker.Mock()
        handler = FlexpoolHandler(notifier=notifier)
        mocker.patch('flexpoolapi.miner')
        mocker.patch('companion.pools.flexpool.FlexpoolHandler._watch_miner_balance')
        get_payements = mocker.patch('companion.pools.flexpool.Miner.get_payements')
        get_payements.return_value = self._create_transactions(new_transactions)
        last_balance, last_transaction = handler.watch_miner(address='addr', last_transaction=old_transaction)
        if new_transactions:
            assert last_transaction == new_transactions[-1]
        else:
            assert last_transaction is None
        if should_notify:
            notifier.notify_payment.assert_called_once()
        else:
            notifier.notify_payment.assert_not_called()

    def test_payment_with_api_failure(self, mocker):
        """An API failure should not send a payment notification"""
        notifier = mocker.Mock()
        notifier.notify_payment = mocker.Mock()
        handler = FlexpoolHandler(notifier=notifier)
        request_get = mocker.patch('requests.get')
        request_get.return_value.status_code = 503
        mocker.patch('companion.pools.flexpool.FlexpoolHandler._watch_miner_balance')
        last_balance, last_transaction = handler.watch_miner(address='0000000000000000000000000000000000000001',
                                                             last_transaction=1)
        assert last_transaction is None
        notifier.notify_payment.assert_not_called()

    @staticmethod
    def _create_blocks(numbers):
        if numbers:
            blocks = []
            for number in numbers:
                blocks.append(BlockApi(number=number, blockhash='h', block_type='bt', miner='m', difficulty=1,
                                       timestamp=1, is_confirmed=True, round_time=1, luck=1.0, server_name='s',
                                       block_reward=1, block_fees=1, uncle_inclusion_rewards=1, total_rewards=1))
            return blocks

    @pytest.mark.parametrize(
        'last_block,remote_blocks,should_notify',
        [
            pytest.param(1, [1, 2], True, id='new_block_with_notification'),
            pytest.param(None, [1], True, id='very_new_block_with_notification'),
            pytest.param(1, [1], False, id='same_block_without_notification'),
            pytest.param(9, range(1, 11), True, id='new_block_with_count_over_max_notification'),
            pytest.param(10, range(1, 11), False, id='same_block_with_count_over_max_notification'),
            pytest.param(None, None, False, id='zero_block_without_notification'),
        ]
    )
    def test_block(self, mocker, last_block, remote_blocks, should_notify):
        notifier = mocker.Mock()
        notifier.notify_block = mocker.Mock()
        handler = FlexpoolHandler(notifier=notifier)
        last_blocks = mocker.patch('flexpoolapi.pool.last_blocks')
        last_blocks.return_value = self._create_blocks(remote_blocks)
        block = handler.watch_blocks(last_block=last_block)
        if remote_blocks:
            assert block == remote_blocks[-1]
        else:
            assert block is None
        if should_notify:
            notifier.notify_block.assert_called_once()
        else:
            notifier.notify_block.assert_not_called()

    def test_block_with_api_failure(self, mocker):
        """An API failure should not send a block notification"""
        notifier = mocker.Mock()
        notifier.notify_block = mocker.Mock()
        handler = FlexpoolHandler(notifier=notifier)
        request_get = mocker.patch('requests.get')
        request_get.return_value.status_code = 503
        block = handler.watch_blocks(last_block=1)
        assert block is None
        notifier.notify_block.assert_not_called()
