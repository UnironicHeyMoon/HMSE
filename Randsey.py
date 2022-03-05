import random
from Asset import Asset
from User import User


class Randsey:
    def __init__(self, all_assets : list[Asset]) -> None:
        self.all_assets = all_assets
        with open("randsey_quotes.txt", "r") as file:
            self.quotes = file.read().split("\n")
    
    def get_randsey_says(self, user : User):
        quote = self.quotes[random.randrange(0, len(self.quotes))]
        asset = self.all_assets[random.randrange(0, len(self.all_assets))]

        quote = quote.replace("RANDOM_STOCK", f"${asset.name}")
        quote = quote.replace("USER", f"@{user.name}")

        to_return = "<hr>\n\n"
        to_return += "Randsey says...\n\n"
        to_return += f":randsey: *{quote}*\n\n"

        return to_return
