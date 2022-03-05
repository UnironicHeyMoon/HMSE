from Asset import Asset
from Command import BuyCommand, Command, ExpiringCommand, SellCommand
from Database import Database
from User import User

class CommandQueue:
    
    def __init__(self, database : Database):
        self.database = database
        self.commands : list[Command] = self.database.get_commands()
        self.has_gotten_commands = True

    def refresh(self):
        self.has_gotten_commands = True
        self.commands = self.database.get_commands()

    def add_command(self, command : Command):
        self.database.add_command(command)
        self.commands.append(command)

    def get_commands(self) -> list[Command]:
        if (not self.has_gotten_commands):
            self.refresh()
        return self.commands

    def delete_command(self, to_delete : Command):
        self.database.delete_command(to_delete)
        self.commands.remove(to_delete)

    def get_transactions_for_user(self, user: User, asset : Asset) -> list[Command]:
        to_return = []
        for command in self.commands:
            if (command.user != user):
                continue
            elif (not isinstance(command, ExpiringCommand)):
                continue
            elif (command.asset != asset):
                continue
            else:
                to_return.append(command)
        return to_return

    def is_selling_asset(self, user : User, asset : Asset) -> bool:
        return len([i for i in self.commands if i.user == user and isinstance(i, SellCommand) and i.asset == asset]) != 0

    def is_buying_asset(self, user : User, asset : Asset) -> bool:
        return len([i for i in self.commands if i.user == user and isinstance(i, BuyCommand) and i.asset == asset]) != 0


    '''
    Returns whether or not we are deleting this
    '''
    def deduct_time(self, to_deduct : ExpiringCommand):
        if (to_deduct not in self.commands):
            return False
        elif (to_deduct.time_remaining == 1):
            self.delete_command(to_deduct)
            return True
        else:
            self.database.set_time_remaining(to_deduct, to_deduct.time_remaining-1)
            self.commands[self.commands.index(to_deduct)].time_remaining = to_deduct.time_remaining-1
            return False