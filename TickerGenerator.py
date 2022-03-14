from Asset import Asset
from Database import Database
from PricePoint import PricePoint
from PriceTracker import PriceTracker
from tabulate import tabulate

class TickerGenerator:
    def __init__(self, pricetracker : PriceTracker, all_assets : list[Asset]) -> None:
        self.pricetracker = pricetracker
        self.all_assets = all_assets
    
    def generate(self):
        headers = ["Stock", "Price", "Last Price", "Daily Average", "Weekly Average", "Monthly Average"]

        rows = []
        for asset in self.all_assets:
            latest : PricePoint = self.pricetracker.get_latest_pricepoint(asset)
            one_hour_ago : PricePoint = self.pricetracker.get_one_hour_ago(asset)
            one_day_ago : PricePoint = self.pricetracker.get_yesterday(asset)
            one_week_ago : PricePoint = self.pricetracker.get_last_week(asset)
            one_month_ago : PricePoint = self.pricetracker.get_last_month(asset)

            current_price = latest.price if latest is not None else 0
            day_average = latest.day_average_price if latest is not None else 0
            week_average = latest.week_average_price if latest is not None else 0
            month_average = latest.month_average_price if latest is not None else 0

            price_one_hour_ago = one_hour_ago.price if one_hour_ago is not None else current_price
            day_average_price_one_day_ago = one_day_ago.day_average_price if one_day_ago is not None else current_price
            week_average_price_one_week_ago = one_week_ago.week_average_price if one_week_ago is not None else current_price
            month_average_price_one_month_ago = one_month_ago.month_average_price if one_month_ago is not None else current_price

            hourly_increase = self.get_growth_percentage(current_price, price_one_hour_ago)
            daily_increase = self.get_growth_percentage(day_average, day_average_price_one_day_ago)
            week_increase = self.get_growth_percentage(week_average, week_average_price_one_week_ago)
            month_increase = self.get_growth_percentage(month_average, month_average_price_one_month_ago)

            rows.append([
                asset.name,
                current_price,
                f"{price_one_hour_ago} ({hourly_increase}%)",
                f"{day_average} ({daily_increase}%)",
                f"{week_average} ({week_increase}%)",
                f"{month_average} ({month_increase}%)"
            ])
        
        return tabulate(rows, headers=headers, tablefmt='html')

            
    def get_growth_percentage(self, a, b):
        if (a == 0 or b == 0):
            return 0
        size = a/b
        growth = 1 - size
        return (int(growth * 100))
