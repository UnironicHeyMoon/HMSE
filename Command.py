from Asset import Asset
from User import User


class Command:
    def __init__(self, id : int, user : User, user_friendly_description : str):
        self._id = id
        self._user = user
        self._user_friendly_description = user_friendly_description

    @property
    def id(self) -> int:
        return self._id

    @property
    def user(self) -> User:
        return self._user

    @property
    def user_friendly_description(self):
        return self._user_friendly_description

    def __str__(self) -> str:
        return self.user_friendly_description
    
    def __repr__(self) -> str:
        return self.user_friendly_description

class ExpiringCommand(Command):
    def __init__(self, id : int, time_remaining : int, user : User, user_friendly_description : str):
        self._time_remaining = time_remaining
        super().__init__(id, user, f"{user_friendly_description} ({time_remaining} TURNS LEFT)")

    @property
    def time_remaining(self) -> int:
        return self._time_remaining

    @time_remaining.setter
    def time_remaining(self, new_time_remaining :int):
        self._time_remaining = new_time_remaining

class BuyCommand(ExpiringCommand):
    def __init__(self, id : int, time_remaining : int, user : User, asset: Asset, max_price : int):
        super().__init__(id, time_remaining, user, f"BUY {asset.name} FOR <= {max_price}")
        self._max_price = max_price
        self._asset = asset
    
    @property
    def max_price(self) -> int:
        return self._max_price 
    
    @property
    def asset(self) -> Asset:
        return self._asset

class SellCommand(ExpiringCommand):
    def __init__(self, id : int, time_remaining : int, user : User, asset: Asset, price : int):
        super().__init__(id, time_remaining, user, f"SELL {asset.name} FOR >= {price}")
        self._price = price
        self._asset = asset

    @property
    def price(self) -> int:
        return self._price 


    @property
    def asset(self) -> Asset:
        return self._asset


class WithdrawalCommand(Command):
    def __init__(self, id : int, amount:int, user : User):
        super().__init__(id, user)
        self._amount = amount

    @property
    def amount(self) -> int:
        return self._amount