import sqlite3

from Command import BuyCommand, Command, ExpiringCommand, SellCommand
from PricePoint import PricePoint
from User import User
from Asset import Asset

from os.path import exists, join, realpath

from Util import get_real_filename

class Database:
    def __init__(self, filename : str) -> None:
        self._con = sqlite3.connect(get_real_filename(filename), timeout=120)
        with open(get_real_filename("setup_database.sql")) as sql_file:
            self._con.executescript(sql_file.read())
    
    def commit(self):
        self.con.commit()

    def rollback(self):
        self.con.rollback()

    def close(self):
        self.con.close()

    @property
    def con(self) -> sqlite3.Connection:
        return self._con

    @property
    def cursor(self) -> sqlite3.Cursor:
        return self.con.cursor()
    
    def get_commands(self) -> list[Command]:
        rows = self.get_rows('''SELECT 
                commands.command_id,
                users.user_id, 
                users.user_name, 
                commands.command_type, 
                commands.amount, 
                assets.asset_id, 
                assets.name, 
                commands.expiring_in 
            FROM ((commands
                INNER JOIN users ON commands.user_id = users.user_id)
                INNER JOIN assets ON commands.asset_id = assets.asset_id)''')
        to_return = []
        for row in rows:
            command_id, user_id, user_name, command_type, amount, asset_id, asset_name, expiring_in = row
            user = User(user_id, user_name)
            asset = Asset(asset_id, asset_name)

            if (command_type == 0):
                command = BuyCommand(command_id, expiring_in, user, asset, amount)
            elif (command_type == 1):
                command = SellCommand(command_id, expiring_in, user, asset, amount)
            else:
                print("Unknown type")
            to_return.append(command)
        return to_return
    
    def delete_command(self, command : Command):
        self.run_command("DELETE FROM commands WHERE command_id = ?", command.id)

    def add_command(self, command : Command):
        #Sanity check: the command should not exist in the table!
        row = self.get_only_row("SELECT * FROM commands WHERE command_id = ?", command.id)
        if (row is not None):
            raise BaseException("That command already exists!")

        self.add_or_update_user(command.user)
        
        expiring_in = None
        if (isinstance(command, ExpiringCommand)):
            expiring_in = command.time_remaining

        amount = None
        if (isinstance(command, BuyCommand)):
            command_type = 0
            amount = command.max_price
        elif (isinstance(command, SellCommand)):
            command_type = 1
            amount = command.price

        self.run_command('''INSERT INTO commands 
            (user_id,
            command_type,
            amount,
            asset_id,
            expiring_in)
        VALUES (?, ?, ?, ?, ?)''', (command.user.id, command_type, amount, command.asset.id, expiring_in))

    def set_time_remaining(self, command : Command, new_time_remaining : int):
        self.run_command("UPDATE commands SET expiring_in = ? WHERE command_id = ?", new_time_remaining, command.id)

    def add_or_update_user(self, user : User, do_update : bool = True):
        results = self.get_only_cell("SELECT user_name FROM users WHERE user_id = ?", user.id)
        if (results is None):
            # Need to create user
            self.run_command("INSERT INTO users (user_id, user_name) VALUES (?, ?)", (user.id, user.name))
        elif (results != user.name and do_update):
            #Need to update name
            self.run_command("UPDATE users SET user_name = ? WHERE user_id = ?", (user.name, user.id))

    def add_asset(self, name):
        self.run_command("INSERT INTO assets (name) VALUES (?)", name)
    
    def get_asset_with_name(self, name):
        id = self.get_only_cell('SELECT asset_id FROM assets WHERE name = ?', name)
        if (id is None):
            return None
        return Asset(id, name)

    def get_all_assets(self) -> list[Asset]:
        rows = self.get_rows('SELECT asset_id, name FROM assets')
        to_return = []
        for row in rows:
            id, name = row
            to_return.append(Asset(id, name)) 
        return to_return

    def create_owned_asset_row_if_does_not_exist(self, user : User, asset : Asset):
        result = self.get_only_row("SELECT * FROM owned_assets WHERE user_id = ? AND asset_id = ?", user.id, asset.id)
        if (result == None):
            self.run_command("INSERT INTO owned_assets (user_id, asset_id) VALUES (?, ?)", user.id, asset.id)

    def set_owned_assets(self, user : User, asset : Asset, number : int = 1):
        self.create_owned_asset_row_if_does_not_exist(user, asset)        
        self.run_command("UPDATE owned_assets SET amount = ? WHERE user_id = ? AND asset_id = ?", number, user.id, asset.id)

    def set_owned_assets_in_escrow(self, user: User, asset: Asset, number : int = 1):
        self.create_owned_asset_row_if_does_not_exist(user, asset)        
        self.run_command("UPDATE owned_assets SET amount_in_escrow = ? WHERE user_id = ? AND asset_id = ?", number, user.id, asset.id)

    def get_owned_assets(self, user: User, asset : Asset):
        return self.get_only_cell_or_zero("SELECT amount FROM owned_assets WHERE user_id = ? AND asset_id = ?", user.id, asset.id)

    def get_owned_assets_in_escrow(self, user: User, asset : Asset):
        return self.get_only_cell_or_zero("SELECT amount_in_escrow FROM owned_assets WHERE user_id = ? AND asset_id = ?", user.id, asset.id)

    def set_price(self, pricepoint : PricePoint):
        time_id = pricepoint.time_id
        asset_id = pricepoint.asset.id
        price = pricepoint.price
        day_average_price = pricepoint.day_average_price
        week_average_price = pricepoint.week_average_price
        month_average_price = pricepoint.month_average_price

        self.run_command('''
            INSERT INTO prices (
                time_id,
                asset_id,
                price,
                day_average_price,
                week_average_price,
                month_average_price
            ) VALUES (
                ?, ?, ?, ?, ?, ?
            )
        ''', time_id, asset_id, price, day_average_price, week_average_price, month_average_price)

    def get_all_prices_in_range(self, min_time_id:int, max_time_id: int, asset : Asset) -> list[PricePoint]:
        rows = self.get_rows('''SELECT 
            assets.asset_id,
            assets.name,
            prices.time_id,
            prices.price,
            prices.day_average_price,
            prices.week_average_price,
            prices.month_average_price
        FROM prices
        INNER JOIN assets ON prices.asset_id = assets.asset_id
        WHERE
            prices.time_id <= ? AND
            prices.time_id >= ? AND
            assets.asset_id = ?
        ''', max_time_id, min_time_id, asset.id)

        to_return = []
        for row in rows:
            asset_id, asset_name, time_id, price, day_average_price, week_average_price, month_average_price = row
            asset = Asset(asset_id, asset_name)
            pricepoint = PricePoint(time_id, asset, price, day_average_price, week_average_price, month_average_price)
            to_return.append(pricepoint)
        return to_return

    def get_closest_price_to_time(self, time_id : int, asset : Asset) -> list[PricePoint]:
        row = self.get_only_row('''SELECT 
            assets.asset_id,
            assets.name,
            prices.time_id,
            prices.price,
            prices.day_average_price,
            prices.week_average_price,
            prices.month_average_price
        FROM prices
        INNER JOIN assets
        ON prices.asset_id = assets.asset_id
        WHERE
            prices.time_id <= ? AND 
            assets.asset_id = ?
        ORDER BY prices.time_id DESC
        LIMIT 1
        ''', time_id, asset.id)

        if (row is None):
            return None
        else:
            asset_id, asset_name, time_id, price, day_average_price, week_average_price, month_average_price = row
            asset = Asset(asset_id, asset_name)
            pricepoint = PricePoint(time_id, asset, price, day_average_price, week_average_price, month_average_price)
            return pricepoint

    def get_balance(self, user: User):
        return self.get_only_cell_or_zero("SELECT balance FROM users WHERE user_id = ?", user.id)
    
    def get_balance_in_escrow(self, user: User):
        return self.get_only_cell_or_zero("SELECT balance_in_escrow FROM users WHERE user_id = ?", user.id)

    def set_balance(self, user: User, amount : int):
        self.add_or_update_user(user)
        self.run_command("UPDATE users SET balance = ? WHERE user_id = ?", amount, user.id)
    
    def set_balance_in_escrow(self, user: User, amount : int):
        self.add_or_update_user(user)
        self.run_command("UPDATE users SET balance_in_escrow = ? WHERE user_id = ?", amount, user.id)

    def create_state_row_if_does_not_exist(self):
        row = self.get_only_row("SELECT * FROM state")
        if (row is None):
            self.run_command("INSERT INTO state (last_processed_notification_id, current_time_id) VALUES (0, 0)")

    def set_last_processed_notification_id(self, id):
        self.create_state_row_if_does_not_exist()
        self.run_command("UPDATE state SET last_processed_notification_id = ?", id)
    
    def get_last_processed_notification_id(self):
        return self.get_only_cell_or_zero("SELECT last_processed_notification_id FROM state")

    def set_current_time_id(self, time_id : int):
        self.create_state_row_if_does_not_exist()
        self.run_command("UPDATE state SET current_time_id = ?", time_id)

    def get_current_time_id(self) -> int:
        return self.get_only_cell_or_zero("SELECT current_time_id FROM state")

    def unpack_nested_tuple(self, my_tuple):
        if (len(my_tuple) != 1 or type(my_tuple[0]) is not tuple):
            return (my_tuple)
        else:
            return self.unpack_nested_tuple(my_tuple[0])

    def run_command(self, command, *args):
        return self.cursor.execute(command, self.unpack_nested_tuple(args))
    
    def get_rows(self, command, *args):
        return self.run_command(command, args).fetchall()
    
    def get_only_row(self, command, *args):
        to_return = self.run_command(command, args).fetchone()
        return to_return
    
    def get_only_cell(self, command, *args):
        row = self.get_only_row(command, args)
        if (row is None):
            return None
        assert (len(row) == 1)
        return row[0]
    
    def get_only_cell_or_zero(self, command, *args):
        result = self.get_only_cell(command, args)
        if (result is None):
            return 0
        else:
            return result