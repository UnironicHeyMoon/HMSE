from Asset import Asset


class PricePoint:
    def __init__(self, time_id: int, asset : Asset, price : int, day_average_price: int, week_average_price: int, month_average_price: int) -> None:
        self.time_id = time_id
        self.asset = asset
        self.price = price
        self.day_average_price = day_average_price
        self.week_average_price = week_average_price
        self.month_average_price = month_average_price