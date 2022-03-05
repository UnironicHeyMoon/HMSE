from dataclasses import dataclass
from Asset import Asset
from Command import Command
from Database import Database
from Log import Log, LogMessageType
from User import User
from RDramaAPIInterface import RDramaAPIInterface

class Bank:
    CLASS_NAME = "BANK"
    def __init__(self, database : Database, log : Log) -> None:
        self.database = database
        self.log = log
    
    '''
    Transfers money from giver's escrow to receiver's balance
    '''
    def transfer(self, giver : User, receiver : User, amount : int):
        giver_initial_balance_in_escrow = self.database.get_balance_in_escrow(giver)
        receiver_initial_balance = self.database.get_balance(receiver)

        giver_new_balance_in_escrow = giver_initial_balance_in_escrow - amount
        receiver_new_balance = receiver_initial_balance + amount

        #Sanity Check
        assert giver_new_balance_in_escrow >= 0, "That would leave the user with negative escrow balance."
        
        self.database.set_balance_in_escrow(giver, giver_new_balance_in_escrow)
        self.database.set_balance(receiver, receiver_new_balance)

        self.log.add_log_message(self.CLASS_NAME, LogMessageType.BANK, f"Transferred {amount} from {giver.name} to {receiver.name}.")

    '''
    Adds new money to depositor's balance.
    '''
    def deposit(self, depositor : User, amount : int):
        assert amount >= 0, "Can't deposit a negative amount of money."
        depositor_initial_balance = self.database.get_balance(depositor)
        new_depositor_balance = depositor_initial_balance + amount
        self.database.set_balance(depositor, new_depositor_balance)

        self.log.add_log_message(self.CLASS_NAME, LogMessageType.BANK, f"Deposited {amount} into {depositor.name}'s account.")

    '''
    Makes a withdrawal from the user's account, and sends appropriate amount of coins to user.
    '''
    def withdrawal(self, withdrawer : User, amount : int):
        assert amount >= 0, "Can't withdraw a negative amount of money."
        withdrawer_initial_balance = self.database.get_balance(withdrawer)
        new_withdrawer_balance = withdrawer_initial_balance - amount
        assert new_withdrawer_balance >= 0, "That would leave the withdrawer with a negative balance."
        self.database.set_balance(withdrawer, new_withdrawer_balance)
        self.log.add_log_message(self.CLASS_NAME, LogMessageType.BANK, f"Withdrew {amount} from {withdrawer.name}'s account.")

    '''
    Gets the current balance of the user's account.
    '''
    def get_balance(self, user : User):
        return self.database.get_balance(user)

    '''
    Gets whether or not a user owns an asset.
    '''
    def has_asset(self, user : User, asset : Asset):
        return self.database.get_owned_assets(user, asset) > 0

    def get_number_of_assets(self, user: User, asset : Asset):
        return self.database.get_owned_assets(user, asset)
    
    def get_number_of_assets_in_escrow(self, user: User, asset : Asset):
        return self.database.get_owned_assets_in_escrow(user, asset)

    '''
    Takes asset from giver's escrow, gives it to receiver's account.
    '''
    def transfer_asset(self, giver : User, receiver : User, asset : Asset):
        initial_giver_number_owned_in_escrow = self.database.get_owned_assets_in_escrow(giver, asset)
        initial_receiver_number_owned = self.database.get_owned_assets(receiver, asset)

        new_giver_number_owned_in_escrow = initial_giver_number_owned_in_escrow - 1
        new_receiver_number_owned = initial_receiver_number_owned + 1

        assert new_giver_number_owned_in_escrow >= 0, "That would leave the giver with less than 0 in escrow"

        self.database.set_owned_assets_in_escrow(giver, asset, new_giver_number_owned_in_escrow)
        self.database.set_owned_assets(receiver, asset, new_receiver_number_owned)

        self.log.add_log_message(self.CLASS_NAME, LogMessageType.BANK, f"Transferred 1 {asset.name} from {giver.name} to {receiver.name}.")
    
    def transfer_asset_to_escrow(self, user : User, asset : Asset, amount : int):
        assert amount > 0, "Cannot transfer a negative number of assets."

        initial_giver_number_owned_in_escrow = self.database.get_owned_assets_in_escrow(user, asset)
        initial_giver_number_owned = self.database.get_owned_assets(user, asset)

        new_giver_number_owned_in_escrow = initial_giver_number_owned_in_escrow + amount
        new_giver_number_owned = initial_giver_number_owned - amount

        assert new_giver_number_owned >= 0, "That would leave the giver with less than zero owned."

        self.database.set_owned_assets_in_escrow(user, asset, new_giver_number_owned_in_escrow)
        self.database.set_owned_assets(user, asset, new_giver_number_owned)

        self.log.add_log_message(self.CLASS_NAME, LogMessageType.BANK, f"Transfer {amount} {asset.name} to {user.name}'s escrow")
    
    def transfer_asset_from_escrow(self, user : User, asset : Asset, amount : int):
        assert amount > 0, "Cannot transfer a negative number of assets"

        initial_giver_number_owned_in_escrow = self.database.get_owned_assets_in_escrow(user, asset)
        initial_giver_number_owned = self.database.get_owned_assets(user, asset)

        new_giver_number_owned_in_escrow = initial_giver_number_owned_in_escrow - amount
        new_giver_number_owned = initial_giver_number_owned + amount

        assert new_giver_number_owned_in_escrow >= 0, "That would leave the giver with less than zero in escrow"

        self.database.set_owned_assets_in_escrow(user, asset, new_giver_number_owned_in_escrow)
        self.database.set_owned_assets(user, asset, new_giver_number_owned)

        self.log.add_log_message(self.CLASS_NAME, LogMessageType.BANK, f"Transfer {amount} {asset.name} from {user.name}'s escrow")

    def transfer_from_escrow(self, user: User, to_transfer : int):
        assert to_transfer > 0, "Cannot transfer a negative amount of money."

        initial_balance_in_escrow = self.database.get_balance_in_escrow(user)
        initial_balance = self.database.get_balance(user)

        new_balance_in_escrow = initial_balance_in_escrow - to_transfer
        new_balance = initial_balance + to_transfer

        assert new_balance_in_escrow >= 0, "That would leave the user with less than zero in escrow"
        self.database.set_balance(user, new_balance)
        self.database.set_balance_in_escrow(user, new_balance_in_escrow)

        self.log.add_log_message(self.CLASS_NAME, LogMessageType.BANK, f"Transfer {to_transfer} from {user.name}'s escrow")
    
    def transfer_to_escrow(self, user: User, to_transfer : int):
        assert to_transfer > 0, "Cannot transfer a negative amount of money."

        initial_balance_in_escrow = self.database.get_balance_in_escrow(user)
        initial_balance = self.database.get_balance(user)

        new_balance_in_escrow = initial_balance_in_escrow + to_transfer
        new_balance = initial_balance - to_transfer

        assert new_balance > 0, "That would leave the giver with less than zero in account"
        self.database.set_balance(user, new_balance)
        self.database.set_balance_in_escrow(user, new_balance_in_escrow)

        self.log.add_log_message(self.CLASS_NAME, LogMessageType.BANK, f"Transfer {to_transfer} to {user.name}'s escrow")

    '''
    Seller sells asset to buyer for price.
    '''
    def sell_asset(self, buyer : User, seller : User, asset : Asset, price : int, buyer_max_price : int):
        self.log.add_log_message(self.CLASS_NAME, LogMessageType.BANK, f"Performing sale of {asset.name}")
        self.transfer(buyer, seller, price)
        self.transfer_asset(seller, buyer, asset)
        if (buyer_max_price > price):
            self.log.add_log_message(self.CLASS_NAME, LogMessageType.BANK, f"Refunding {buyer_max_price - price} into {buyer.name}'s account")
            remaining_in_escrow = buyer_max_price - price
            self.transfer_from_escrow(buyer, remaining_in_escrow)
