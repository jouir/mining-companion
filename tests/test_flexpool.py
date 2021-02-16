from datetime import datetime, timedelta

import pytest
from companion.pools.flexpool import FlexpoolHandler, Transaction


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
