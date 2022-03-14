from typing import Callable
from numpy import average
from Asset import Asset
from Database import Database
from PricePoint import PricePoint

DAY_LENGTH = 24
WEEK_LENGTH = DAY_LENGTH*7
MONTH_LENGTH = WEEK_LENGTH*7

class PriceTracker:
    def __init__(self, database : Database) -> None:
        self.database = database
    
    def set_price(self, asset: Asset, price : int, time : int = None):
        if time is None:
            current_time = self.database.get_current_time_id()
        else:
            current_time = time
        prices_in_day = self.database.get_all_prices_in_range(current_time - DAY_LENGTH, current_time, asset)
        day_average_price = self.get_average_price(prices_in_day, lambda a: a.price, price)

        pricepoints_in_week = self.database.get_all_prices_in_range(current_time - WEEK_LENGTH, current_time, asset)
        week_average_price = self.get_average_price(pricepoints_in_week, lambda a : a.price, price)

        pricepoints_in_month = self.database.get_all_prices_in_range(current_time - MONTH_LENGTH, current_time, asset)
        month_average_price = self.get_average_price(pricepoints_in_month, lambda a : a.price, price)

        pricepoint = PricePoint(current_time, asset, price, day_average_price, week_average_price, month_average_price)
        self.database.set_price(pricepoint)

    def get_latest_pricepoint(self, asset : Asset) -> PricePoint:
        current_time = self.database.get_current_time_id()
        last_pricepoint = self.database.get_closest_price_to_time(current_time, asset)
        return last_pricepoint

    def maintain_price(self, asset : Asset):
        last_price = self.get_latest_pricepoint(asset)
        if (last_price is None):
            last_price = 0
        else:
            last_price = last_price.price
        self.set_price(asset, last_price)

    def get_pricepoint_in_past(self, asset : Asset, time_in_past : int) -> PricePoint:
        current_time = self.database.get_current_time_id()
        pricepoint = self.database.get_closest_price_to_time(current_time - time_in_past, asset)
        return pricepoint

    def get_one_hour_ago(self, asset: Asset) -> PricePoint:
        return self.get_pricepoint_in_past(asset, 1)

    def get_yesterday(self, asset : Asset) -> PricePoint:
        return self.get_pricepoint_in_past(asset, DAY_LENGTH)
    
    def get_last_week(self, asset : Asset) -> PricePoint:
        return self.get_pricepoint_in_past(asset, WEEK_LENGTH)
    
    def get_last_month(self, asset : Asset) -> PricePoint:
        return self.get_pricepoint_in_past(asset, MONTH_LENGTH)

    def get_average_price(self, pricepoints : list[PricePoint], get_price : Callable[[PricePoint], int], default_price: int) -> int:
        prices = [get_price(pricepoint) for pricepoint in pricepoints if pricepoint is not None]
        if (len(prices) != 0):
            return int(average(prices))
        else:
            return default_price





