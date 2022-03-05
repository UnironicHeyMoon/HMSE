from cgi import test
import random
import unittest
from unittest.mock import MagicMock
from Asset import Asset
from Bank import Bank
from Command import SellCommand
from CommandQueue import CommandQueue
from Command import Command
from Command import BuyCommand
from MessageManager import MessageManager
from StockExchange import StockExchange
from User import User

def assert_not_called_with(self, *args, **kwargs):
    try:
        self.assert_called_with(*args, **kwargs)
    except AssertionError:
        return
    raise AssertionError('Expected %s to not have been called.' % self._format_mock_call_signature(args, kwargs))

MagicMock.assert_not_called_with = assert_not_called_with

def create_user() -> User:
    return User(random.randrange(1, 5000), "Eggbert")

def create_asset(name: str = None) -> Asset:
    if (name != None):
        return Asset(random.randrange(1, 5000), name)
    else:
        return Asset(random.randrange(1, 5000), str(random.randrange(1, 5000)))

def create_sell_command(time_remaining : int = 2, user : User = create_user(), asset : Asset = create_asset(), price: int = 40) -> SellCommand:
    return SellCommand(random.randrange(1, 5000), time_remaining, user, asset, price)

def create_buy_command(time_remaining : int = 2, user : User = create_user(), asset : Asset = create_asset(), max_price: int = 500) -> BuyCommand:
    return BuyCommand(random.randrange(1, 5000), time_remaining, user, asset, max_price)

def create_command_queue(commands : list[Command]) -> CommandQueue:
    commandQueue : CommandQueue = CommandQueue()
    commandQueue.get_commands = MagicMock(return_value = commands)
    commandQueue.deduct_time = MagicMock()
    commandQueue.delete_command = MagicMock()
    return commandQueue

def create_bank(balance : int = 700, has_asset : bool = True):
    bank : Bank = Bank()
    bank.get_balance = MagicMock(return_value = balance)
    bank.has_asset = MagicMock(return_value = has_asset)
    bank.transfer = MagicMock()
    bank.transfer_asset = MagicMock()
    return bank

class StockExchangeTests(unittest.TestCase):
    def test_sell_with_no_buyers(self):
        my_sell_command : SellCommand = create_sell_command()

        commandQueue : CommandQueue = create_command_queue([my_sell_command])
        bank : Bank = create_bank()
        messageManager : MessageManager = MessageManager(None)

        stockExchange : StockExchange = StockExchange(commandQueue, bank, messageManager)
        stockExchange.process()

        commandQueue.deduct_time.assert_called_with(my_sell_command)
        bank.transfer.assert_not_called()
        bank.transfer_asset.assert_not_called()
        commandQueue.delete_command.assert_not_called()
    
    def test_buy_with_no_sellers(self):
        my_buy_command : BuyCommand = create_buy_command()

        commandQueue : CommandQueue = create_command_queue([my_buy_command])
        bank : Bank = create_bank()
        messageManager : MessageManager = MessageManager(None)

        stockExchange : StockExchange = StockExchange(commandQueue, bank, messageManager)
        stockExchange.process()

        commandQueue.deduct_time.assert_called_with(my_buy_command)
        bank.transfer.assert_not_called()
        bank.transfer_asset.assert_not_called()
        commandQueue.delete_command.assert_not_called()

    def test_buying_and_selling_happy_path(self):
        asset : Asset = create_asset("My Stock")
        buyer : User = create_user()
        seller : User = create_user()
        my_buy_command : BuyCommand = create_buy_command(max_price=500, asset=asset, user=buyer)
        my_sell_command : SellCommand = create_sell_command(price=40, asset=asset, user=seller)

        commandQueue : CommandQueue = create_command_queue([my_buy_command, my_sell_command])
        bank : Bank = create_bank()
        messageManager : MessageManager = MessageManager(None)

        stockExchange : StockExchange = StockExchange(commandQueue, bank, messageManager)
        stockExchange.process()

        commandQueue.delete_command.assert_any_call(my_buy_command)
        commandQueue.delete_command.assert_any_call(my_sell_command)
        bank.transfer.assert_any_call(buyer, seller, 40)
        bank.transfer_asset.assert_any_call(seller, buyer, asset)
    
    def test_buying_and_selling_different_assets(self):
        asset_a : Asset = create_asset()
        asset_b : Asset = create_asset()
        buyer : User = create_user()
        seller : User = create_user()
        my_buy_command : BuyCommand = create_buy_command(max_price=500, asset=asset_a, user=buyer)
        my_sell_command : SellCommand = create_sell_command(price=40, asset=asset_b, user=seller)

        commandQueue : CommandQueue = create_command_queue([my_buy_command, my_sell_command])
        bank : Bank = create_bank()
        messageManager : MessageManager = MessageManager(None)

        stockExchange : StockExchange = StockExchange(commandQueue, bank, messageManager)
        stockExchange.process()

        commandQueue.delete_command.assert_not_called()
        bank.transfer.assert_not_called()
        bank.transfer_asset.assert_not_called()

    def test_lowest_selling_bid_gets_first_priority(self):
        asset : Asset = create_asset()
        buyer : User = create_user()
        low_seller : User = create_user()
        high_seller : User = create_user()
        my_buy_command : BuyCommand = create_buy_command(max_price=500, asset=asset, user=buyer)
        low_sell_command : SellCommand = create_sell_command(price=40, asset=asset, user=low_seller)
        high_sell_command : SellCommand = create_sell_command(price=80, asset=asset, user=high_seller)

        commandQueue : CommandQueue = create_command_queue([my_buy_command, low_sell_command, high_sell_command])
        bank : Bank = create_bank()
        messageManager : MessageManager = MessageManager(None)

        stockExchange : StockExchange = StockExchange(commandQueue, bank, messageManager)
        stockExchange.process()

        commandQueue.delete_command.assert_any_call(my_buy_command)
        commandQueue.delete_command.assert_any_call(low_sell_command)
        commandQueue.delete_command.assert_not_called_with(high_sell_command)
        bank.transfer.assert_any_call(buyer, low_seller, 40)
        bank.transfer.assert_not_called_with(buyer, high_seller, 80)
        bank.transfer_asset.assert_any_call(low_seller, buyer, asset)
        bank.transfer_asset.assert_not_called_with(high_seller, buyer, asset)

    def test_lowest_buying_bid_gets_first_priority(self):
        asset : Asset = create_asset()
        low_buyer : User = create_user()
        high_buyer : User = create_user()
        seller : User = create_user()
        low_buy_command : BuyCommand = create_buy_command(max_price=50, asset=asset, user=low_buyer)
        high_buy_command : BuyCommand = create_buy_command(max_price=70, asset=asset, user=high_buyer)
        sell_command : SellCommand = create_sell_command(price=40, asset=asset, user=seller)

        commandQueue : CommandQueue = create_command_queue([low_buy_command, high_buy_command, sell_command])
        bank : Bank = create_bank()
        messageManager : MessageManager = MessageManager(None)

        stockExchange : StockExchange = StockExchange(commandQueue, bank, messageManager)
        stockExchange.process()

        commandQueue.delete_command.assert_any_call(sell_command)
        commandQueue.delete_command.assert_any_call(low_buy_command)
        commandQueue.delete_command.assert_not_called_with(high_buy_command)
        bank.transfer.assert_any_call(low_buyer, seller, 40)
        bank.transfer.assert_not_called_with(high_buyer, seller, 80)
        bank.transfer_asset.assert_any_call(seller, low_buyer, asset)
        bank.transfer_asset.assert_not_called_with(seller, high_buyer, asset)

if __name__ == '__main__':
    unittest.main()