import copy
from pprint import pprint
from re import A
from typing import Callable

from numpy import average
from Asset import Asset
from Bank import Bank
from Command import BuyCommand, Command, ExpiringCommand, SellCommand, WithdrawalCommand
from CommandQueue import CommandQueue
from Database import Database
from MessageManager import MessageManager, MessageType
from PriceTracker import PriceTracker
from User import User


class StockExchange:
    def __init__(self) -> None:
        pass
    
    def get_sales(self, commands : list[Command], all_assets : list[Asset]) -> dict[Asset, dict]:
        selling_assets : dict[Asset, list[SellCommand]] = StockExchange.create_sell_command_groups(commands)
        buying_assets : dict[Asset, list[BuyCommand]] = StockExchange.create_buy_command_groups(commands)
        
        to_return = {}

        for asset, buy_offers in buying_assets.items():
            to_return[asset] = {}
            to_return[asset]['sell_offers'] = []
            to_return[asset]['buy_offers'] = buy_offers
            to_return[asset]['completed_sales'] = []
            to_return[asset]['dead_market'] = False
            to_return[asset]['buyers_market'] = False
            to_return[asset]['failed_sales'] = {}
            to_return[asset]['failed_sales']['outbidded'] = []
            to_return[asset]['failed_sales']['no_sellers'] = []
            to_return[asset]['failed_sales']['no_buyers'] = []
            to_return[asset]['failed_sales']['stingy'] = []
            to_return[asset]['failed_sales']['outpriced'] = []
            if (asset in selling_assets):
                to_return[asset]['dead_market'] = False
                sell_offers = selling_assets[asset]
                to_return[asset]['sell_offers'] = copy.copy(sell_offers)
                sell_offers.sort(key = lambda a : a.price)
                buy_offers.sort(key = lambda a : a.max_price, reverse=True)

                buyers_market : bool
                if (len(sell_offers) > len(buy_offers)):
                    buyers_market = True
                else:
                    buyers_market = False
                to_return[asset]['buyers_market'] = buyers_market

                for buy_offer in buy_offers:

                    #Get the cheapest asset in the list
                    if (len(sell_offers) > 0):
                        sell_offer = sell_offers[0]
                    else:
                        # If there are no more assets to buy, buyer was outbidded
                        assert not buyers_market
                        to_return[asset]['failed_sales']['outbidded'].append(buy_offer)
                        continue
                    
                    #Establish sale price. If a buyer's market, we use the seller's min price. If a seller's market, we use buyer's max price.
                    sale_price: int
                    if (buyers_market):
                        sale_price = sell_offer.price
                        if (sale_price > buy_offer.max_price):
                            #weird scenario where it's a buyer's market but the price is too low.
                            to_return[asset]['failed_sales']['stingy'].append(buy_offer)
                            continue
                    else:
                        sale_price = buy_offer.max_price

                    #Can buy
                    to_return[asset]['completed_sales'].append({
                        'sell_command' : sell_offer,
                        'buy_command' : buy_offer,
                        'sale_price' : sale_price,
                        'price': sell_offer.price,
                        'max_price': buy_offer.max_price
                    })

                    #Remove the seller from the remaining sellers.
                    sell_offers.pop(0)
                
                #If there are any sales left over, those were outpriced - ie, their prices weren't competitive enough for the few buyers on the market.
                if (len(sell_offers) > 0):
                    to_return[asset]['failed_sales']['outpriced'] = sell_offers
            else:
                #Dead seller's market
                to_return[asset]['dead_market'] = True
                to_return[asset]['buyers_market'] = False
                to_return[asset]['failed_sales']['no_sellers'] = buy_offers

        for asset in all_assets:
            if (asset not in to_return):
                #Dead buyer's market
                to_return[asset] = {}
                to_return[asset]['buy_offers'] = []
                to_return[asset]['dead_market'] = True
                to_return[asset]['buyers_market'] = True
                to_return[asset]['failed_sales'] = {}
                to_return[asset]['completed_sales'] = []
                to_return[asset]['failed_sales']['outbidded'] = []
                to_return[asset]['failed_sales']['no_sellers'] = []
                to_return[asset]['failed_sales']['stingy'] = []
                to_return[asset]['failed_sales']['outpriced'] = []
                to_return[asset]['failed_sales']['no_buyers'] = selling_assets[asset] if asset in selling_assets else []
                to_return[asset]['sell_offers'] = selling_assets[asset] if asset in selling_assets else []
        
        return to_return

    def group_objects(objects_to_group: list[object], is_object_valid : Callable[[object], bool], get_grouping_key: Callable[[object], object]) -> dict[object, list[object]]:
        objects : list[object] = list(filter(lambda a : is_object_valid(a), objects_to_group))
        to_return : dict[object, list[object]] = {}

        for an_object in objects:
            if (an_object.asset not in to_return):
                to_return[an_object.asset] = []
            to_return[an_object.asset].append(an_object)
        
        return to_return

    def create_sell_command_groups(commands : list[Command]) -> dict[Asset, list[SellCommand]]:
        return StockExchange.group_objects(commands, lambda a : isinstance(a, SellCommand), lambda a : a.asset)
    
    def create_buy_command_groups(commands : list[Command]) -> dict[Asset, list[BuyCommand]]:
        return StockExchange.group_objects(commands, lambda a : isinstance(a, BuyCommand), lambda a : a.asset)