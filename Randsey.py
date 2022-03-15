import random
from Asset import Asset
from User import User
from os.path import exists, join, realpath

from Util import get_real_filename

class Randsey:
    def __init__(self, all_assets : list[Asset]) -> None:
        self.all_assets = all_assets
        with open(get_real_filename("randsey_quotes.txt")) as file:
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

if __name__ == '__main__':
    randsey = Randsey([Asset(1, "PUTIN")])
    print(randsey.get_randsey_says(User(1, "HeyMoon")))