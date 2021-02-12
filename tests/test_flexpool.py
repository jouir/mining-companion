from companion.pools.flexpool import FlexpoolHandler, Miner, Transaction
from datetime import datetime, timedelta
import pytest

class TestFlexpoolHandler:
    # def test_block(self, mocker):
    def test_init(self):
        handler = FlexpoolHandler()
        assert handler.pool_name == 'flexpool'

    def test_new_balance_with_notification(self, mocker):
        """Old balance is 1, new balance is 2, should send notification"""
        notifier = mocker.Mock()
        notifier.notify_balance = mocker.Mock()
        handler = FlexpoolHandler(notifier=notifier)
        miner = mocker.patch('flexpoolapi.miner')
        miner().balance.return_value = 2
        mocker.patch('companion.pools.flexpool.FlexpoolHandler._watch_miner_payments')
        mocker.patch('companion.pools.flexpool.Miner.get_payements')
        last_balance, last_transaction = handler.watch_miner(address='addr', last_balance=1)
        assert last_balance == 2
        notifier.notify_balance.assert_called_once()

    def test_new_balance_after_payment_with_notification(self, mocker):
        """Old balance is 0, new balance is 1 (old > new), should send notification"""
        notifier = mocker.Mock()
        notifier.notify_balance = mocker.Mock()
        handler = FlexpoolHandler(notifier=notifier)
        miner = mocker.patch('flexpoolapi.miner')
        miner().balance.return_value = 0
        mocker.patch('companion.pools.flexpool.FlexpoolHandler._watch_miner_payments')
        mocker.patch('companion.pools.flexpool.Miner.get_payements')
        last_balance, last_transaction = handler.watch_miner(address='addr', last_balance=1)
        assert last_balance == 0
        notifier.notify_balance.assert_called_once()

    def test_very_new_balance_with_notification(self, mocker):
        """Old balance doesn't exist, new balance is 1, should send notification"""
        notifier = mocker.Mock()
        notifier.notify_balance = mocker.Mock()
        handler = FlexpoolHandler(notifier=notifier)
        miner = mocker.patch('flexpoolapi.miner')
        miner().balance.return_value = 1
        mocker.patch('companion.pools.flexpool.FlexpoolHandler._watch_miner_payments')
        mocker.patch('companion.pools.flexpool.Miner.get_payements')
        last_balance, last_transaction = handler.watch_miner(address='addr')
        assert last_balance == 1
        notifier.notify_balance.assert_called_once()

    def test_same_balance_without_notification(self, mocker):
        """Old balance and new balance are the same, should not send notification"""
        notifier = mocker.Mock()
        notifier.notify_balance = mocker.Mock()
        handler = FlexpoolHandler(notifier=notifier)
        miner = mocker.patch('flexpoolapi.miner')
        miner().balance.return_value = 1
        mocker.patch('companion.pools.flexpool.FlexpoolHandler._watch_miner_payments')
        mocker.patch('companion.pools.flexpool.Miner.get_payements')
        last_balance, last_transaction = handler.watch_miner(address='addr', last_balance=1)
        assert last_balance == 1
        notifier.notify_balance.assert_not_called()

    def test_new_payment_with_notification(self, mocker):
        """One transaction saved (trx1), two transactions detected (trx1, trx2), should send notification"""
        notifier = mocker.Mock()
        notifier.notify_payment = mocker.Mock()
        handler = FlexpoolHandler(notifier=notifier)
        mocker.patch('flexpoolapi.miner')
        mocker.patch('companion.pools.flexpool.FlexpoolHandler._watch_miner_balance')
        get_payements = mocker.patch('companion.pools.flexpool.Miner.get_payements')
        get_payements.return_value = [
            Transaction(txid='trx1', amount=1, time=datetime.now(), duration=timedelta(minutes=1)),
            Transaction(txid='trx2', amount=1, time=datetime.now(), duration=timedelta(minutes=1))
        ]
        last_balance, last_transaction = handler.watch_miner(address='addr', last_transaction='trx1')
        assert last_transaction == 'trx2'
        notifier.notify_payment.assert_called_once()

    def test_very_new_payment_with_notification(self, mocker):
        """No transaction saved, one transaction detected (trx1), should send notification"""
        notifier = mocker.Mock()
        notifier.notify_payment = mocker.Mock()
        handler = FlexpoolHandler(notifier=notifier)
        mocker.patch('flexpoolapi.miner')
        mocker.patch('companion.pools.flexpool.FlexpoolHandler._watch_miner_balance')
        get_payements = mocker.patch('companion.pools.flexpool.Miner.get_payements')
        get_payements.return_value = [
            Transaction(txid='trx1', amount=1, time=datetime.now(), duration=timedelta(minutes=1))
        ]
        last_balance, last_transaction = handler.watch_miner(address='addr', last_transaction=None)
        assert last_transaction == 'trx1'
        notifier.notify_payment.assert_called_once()

    def test_same_payment_without_notification(self, mocker):
        """One transaction saved (trx1), one transaction detected (trx1), should not send notification"""
        notifier = mocker.Mock()
        notifier.notify_payment = mocker.Mock()
        handler = FlexpoolHandler(notifier=notifier)
        mocker.patch('flexpoolapi.miner')
        mocker.patch('companion.pools.flexpool.FlexpoolHandler._watch_miner_balance')
        get_payements = mocker.patch('companion.pools.flexpool.Miner.get_payements')
        get_payements.return_value = [
            Transaction(txid='trx1', amount=1, time=datetime.now(), duration=timedelta(minutes=1))
        ]
        last_balance, last_transaction = handler.watch_miner(address='addr', last_transaction='trx1')
        assert last_transaction == 'trx1'
        notifier.notify_payment.assert_not_called()

    def test_zero_payment_without_notification(self, mocker):
        """Zero transaction saved, zero transaction detected, should not send notification"""
        notifier = mocker.Mock()
        notifier.notify_payment = mocker.Mock()
        handler = FlexpoolHandler(notifier=notifier)
        mocker.patch('flexpoolapi.miner')
        mocker.patch('companion.pools.flexpool.FlexpoolHandler._watch_miner_balance')
        get_payements = mocker.patch('companion.pools.flexpool.Miner.get_payements')
        get_payements.return_value = []
        last_balance, last_transaction = handler.watch_miner(address='addr', last_transaction=None)
        assert last_transaction is None
        notifier.notify_payment.assert_not_called()
