TEST = True

from pprint import pprint
import sys
import traceback

from numpy import average
from Asset import Asset
from Command import BuyCommand, Command, ExpiringCommand, SellCommand
from CommandQueue import CommandQueue
from Log import Log, LogMessageType
from MessageManager import MessageManager, MessageType
from Parser import Parser
from Bank import Bank
from Database import Database
from PriceTracker import PriceTracker
from RDramaAPIInterface import TEST_AUTH_TOKEN, RDramaAPIInterface
from Randsey import Randsey
from StockExchange import StockExchange
from TickerGenerator import TickerGenerator
from User import User
from tabulate import tabulate


class HMSE:
    CLASS_NAME = "HMSE"

    def __init__(self, api : RDramaAPIInterface, database : Database, bank : Bank, parser : Parser, commandQueue : CommandQueue, log : Log):
        self.all_assets = database.get_all_assets()
        self.api = api
        self.bank = bank
        self.database = database
        self.parser = parser
        self.commandQueue = commandQueue
        self.randsey = Randsey(self.all_assets)
        self.messageManager = MessageManager(api, self.randsey) 
        self.priceTracker = PriceTracker(self.database)
        self.stockExchange = StockExchange()
        self.log = log
        self.tickerGenerator = TickerGenerator(self.priceTracker, self.all_assets)

    def update(self):
        try:
            last_processed_notification_id = self.database.get_last_processed_notification_id()
            notifications = self.api.get_parsed_notification(last_processed_notification_id)
            new_notifications = [i['id'] for i in notifications]
            if (new_notifications != []):
                new_last_processed_notification_id = new_notifications[0]
                self.database.set_last_processed_notification_id(new_last_processed_notification_id)
            else:
                new_last_processed_notification_id = last_processed_notification_id

        except BaseException as e:
            self.log.add_log_message(self.CLASS_NAME, LogMessageType.EXCEPTION, f"Exception occurred in last_processed_notification_id: {e}")
            self.database.rollback()
            return
        finally:
            self.database.commit()
        
        self.log.add_log_message(self.CLASS_NAME, LogMessageType.UPDATE, f"Updating. There are {len(notifications)} to process. Previous Last Processed = {last_processed_notification_id}, New Last processed = {new_last_processed_notification_id}")

        for notification in notifications:
            if 'user_name' in notification and 'user_id' in notification:
                user = User(notification['user_id'], notification['user_name'])
            else:
                user = None
            self.log.add_log_message(self.CLASS_NAME, LogMessageType.PROCESS_NOTIFICATION, str(notification), user=user)

            try:
                if notification['type'] == 'transfer':
                    self.bank.deposit(user, notification['amount'])
                    message = f"Deposited {notification['amount']} in your account."
                    message += self.randsey.get_randsey_says(user)
                    self.api.send_message(user.name, message)
                    self.log.add_log_message(self.CLASS_NAME, LogMessageType.DEPOSIT, str(notification['amount']), user=user)
                elif notification['type'] == 'post_mention':
                    self.api.reply_to_comment_easy(notification['id'], notification['post_id'], ":randsey: You rang?")
                elif notification['type'] == 'follow':
                    self.api.send_message(user.name, f":randsey: *If it isn't {user.name}. Don't expect any special favors.* {self.randsey.get_randsey_says(user)}")
                elif notification['type'] == 'unfollow':
                    self.api.send_message(user.name, f":randsey: *Well, fuck you too, I guess.* {self.randsey.get_randsey_says(user)}")
                elif notification['type'] == 'comment_reply':
                    for reply in notification['replies']:
                        user = User(int(reply['user_id']), reply['user_name'])
                        response = self.handle_command(user, reply['message'])
                        self.api.reply_to_comment_easy(reply['id'], notification['post_id'], response)
                elif notification['type'] == 'direct_message':
                    response = self.handle_command(user, notification['message_html'])
                    self.api.reply_to_direct_message(notification['id'], str(response))
                elif notification['type'] == 'comment_mention':
                    response = self.handle_command(user, notification['message'])
                    self.api.reply_to_comment_easy(notification['id'], notification['post_id'], str(response))
            except BaseException as e:
               print(f"=====Exception occurred!=====")
               print("While processing this notification:")
               pprint(notification)
               print(f"We got: \"{e}\"")
               print(traceback.format_exc())
               self.log.add_log_message(self.CLASS_NAME, LogMessageType.EXCEPTION, f"While processing notification: {traceback.format_exc()}")
               self.database.rollback()
            else:
               self.database.commit()

    '''
    handles command, returns some messaging around what happened.
    '''
    def handle_command(self, user : User, message : str) -> str:
        command = self.parser.parse_message(message)
        to_return = ""

        try:
            if (command['type'] == "BALANCE"):
                #todo: add more information about owned stocks
                balance = self.database.get_balance(user)
                balance_in_escrow = self.database.get_balance_in_escrow(user)
                to_return = f"Currently, you have {balance + balance_in_escrow} coins in your account. Of these, {balance} are available, and the rest are in escrow."

                headers = ["What", "Available", "In Escrow", "Total"]
                rows = []
                rows.append (
                    [
                        "(coins)",
                        balance,
                        balance_in_escrow,
                        balance + balance_in_escrow
                    ]
                )

                for asset in self.all_assets:
                    owned_available = self.bank.get_number_of_assets(user, asset)
                    owned_in_escrow = self.bank.get_number_of_assets_in_escrow(user, asset)
                    owned_total = owned_available + owned_in_escrow

                    if (owned_total != 0):
                        rows.append(
                            [
                                asset.name,
                                owned_available,
                                owned_in_escrow,
                                owned_total
                            ]
                        )

                rows.append(
                    [
                        "BITCHES",
                        0,
                        0,
                        0
                    ]
                )

                to_return += tabulate(rows, headers=headers, tablefmt='html')
            elif (command['type'] == "BUY"):
                asset = self.database.get_asset_with_name(command['asset'].upper())
                max_price = int(command['max_price'])
                count = int(command['count'])
                time_remaining = int(command['time_remaining'])

                if (self.bank.get_balance(user) < max_price * count): #Make sure that user has enough for max...
                    to_return = "You don't have enough money! lmao"
                elif (self.commandQueue.is_selling_asset(user, asset)):
                    to_return = "You aren't allowed to buy and sell an asset at the same time, Schlomo."
                else:
                    self.bank.transfer_to_escrow(user, max_price * count)
                    for i in range(count):
                        command = BuyCommand(None, time_remaining, user, asset, max_price)
                        self.commandQueue.add_command(command)
                    to_return = f"Placed a BUY order for {count} share(s) of {asset.name} for a maximum price of {max_price}, expiring in {time_remaining} turns."
                    self.log.add_log_message(self.CLASS_NAME, LogMessageType.PLACE_BUY_COMMANDS, to_return, user=user)
            elif (command['type'] == "SELL"):
                asset = self.database.get_asset_with_name(command['asset'].upper())
                price = int(command['price'])
                count = int(command['count'])
                time_remaining = int(command['time_remaining'])

                if (self.bank.get_number_of_assets(user, asset) < count): #Make sure that user has enough assets...
                    to_return = "You don't have enough shares! lmao"
                elif (self.commandQueue.is_buying_asset(user, asset)):
                    to_return = "You aren't allowed to buy and sell an asset at the same time, Schlomo."
                else:
                    self.bank.transfer_asset_to_escrow(user, asset, count)
                    for i in range(count):
                        command = SellCommand(None, time_remaining, user, asset, price)
                        self.commandQueue.add_command(command)
                    to_return = f"Placed a SELL order for {count} share(s) of {asset.name} for a minimum price of {price}, expiring in {time_remaining} turns."
                    self.log.add_log_message(self.CLASS_NAME, LogMessageType.PLACE_SELL_COMMANDS, to_return, user=user)
            elif (command['type'] == "CANCEL"):
                asset = self.database.get_asset_with_name(command['asset'].upper())
                commands = self.commandQueue.get_transactions_for_user(user, asset)

                for i in commands:
                    if (isinstance(i, BuyCommand)):
                        self.bank.transfer_from_escrow(user, i.max_price)
                        self.commandQueue.delete_command(i)
                        to_return += f"Canceled {i}. Refunded {i.max_price}\n"
                    elif (isinstance(i, SellCommand)):
                        self.bank.transfer_asset_from_escrow(user, asset, 1)
                        self.commandQueue.delete_command(i)
                        to_return += f"Canceled {i}. Refunded 1 {asset.name}\n"
                    else:
                        to_return += f"Couldn't cancel {i}.\n"
                self.log.add_log_message(self.CLASS_NAME, LogMessageType.CANCEL_COMMANDS, to_return, user=user)
            elif (command['type'] == "WITHDRAW"):
                amount = int(command['amount'])
                if (self.bank.get_balance(user) < amount):
                    to_return = "Nice try. You don't have enough balance for that."
                else:
                    self.bank.withdrawal(user, amount)
                    self.api.give_coins(user.name, amount)
                    to_return = f"Withdrew {amount}."
                    self.log.add_log_message(self.CLASS_NAME, LogMessageType.WITHDRAWAL, to_return, user=user)
            elif (command['type'] == "MARKET"):
                asset = self.database.get_asset_with_name(command['asset'].upper())
                market_status = self.stockExchange.get_sales(self.commandQueue.get_commands(), self.all_assets)[asset]
                
                to_return = f"There are {len(market_status['sell_offers'])} sellers and {len(market_status['buy_offers'])} buyers. "
                if (market_status['buyers_market']):
                    to_return+="That makes the market a *buyer's market*, meaning that the buyer will pay the seller's price."
                else:
                    to_return+="That makes the market a *seller's market*, meaning that the buyer will pay the buyer's max price."
                
                to_return += "\n\n"
                buy_offers = [i.max_price for i in market_status['buy_offers']]
                sell_offers = [i.price for i in market_status['sell_offers']]
                completed_sale_max_prices = [i['max_price'] for i in market_status['completed_sales']]
                completed_sale_sellers_prices = [i['price'] for i in market_status['completed_sales']]
                if (buy_offers != []):
                    buy_offers.sort()
                    to_return += f"Highest Bid: {buy_offers[-1]}\n\n"
                if (completed_sale_max_prices != []):
                    completed_sale_max_prices.sort()
                    to_return += f"Lowest Winning Bid: {completed_sale_max_prices[0]}\n\n"
                if (sell_offers != []):
                    sell_offers.sort()
                    to_return += f"Lowest Asking Price: {sell_offers[0]}\n\n"
                if (completed_sale_sellers_prices != []):
                    completed_sale_sellers_prices.sort()
                    to_return += f"Highest Winning Asking Price: {completed_sale_sellers_prices[0]}\n\n"
                
            elif (command['type'] == "TICKER"):
                to_return = self.tickerGenerator.generate()
            elif (command['type'] == "TREND"):
                to_return = "This doesn't work, unfortunately. I can't figure out how to attach images :marseyshrug:"
            elif (command['type'] == "RANDSEY"):
                to_return = "Paging randsey..."
            elif (command['type'] == "UNKNOWN"):
                to_return = f"Sorry, I didn't understand that. \"{command['unrecognized_command']}\" is not a valid command."
            elif (command['type'] == "MALFORMED"):
                to_return = f"Malformed command. exception = {command['exception']}"
                self.log.add_log_message(self.CLASS_NAME, LogMessageType.MALFORMED, str(command['exception']), user=user)
            else:
                to_return = "Huh. That's weird."
        except AssertionError as e:
            print(f"=====Jewshit occurred!=====")
            print(f"While processing this message (from {user.name}):")
            pprint(message)
            print(f"We got: \"{e}\"")
            print(traceback.format_exc())
            to_return = f"Nice try, jew. I thought of that edge condition. :marseysmug: Error was: {e}"
            to_return += f"If this was, in fact, not jewshit, let @HeyMoon know and he will clean it up."
            self.log.add_log_message(self.CLASS_NAME, LogMessageType.JEWRY, traceback.format_exc(), user=user)
            self.database.rollback()
        except BaseException as e:
            print(f"=====Exception occurred!=====")
            print(f"While processing this message (from {user.name}):")
            pprint(message)
            print(f"We got: \"{e}\"")
            print(traceback.format_exc())
            to_return = f"Something got messed up :( The error was {e}. Please bitch and moan at @HeyMoon to clean it up. Thanks :marseylove:\n"
            to_return += "Note that your command was not processed."
            self.log.add_log_message(self.CLASS_NAME, LogMessageType.EXCEPTION, traceback.format_exc(), user=user)
            self.database.rollback()
        else:
            self.database.commit()
        to_return += self.randsey.get_randsey_says(user)
        return to_return

    def process(self):
        self.log.add_log_message(self.CLASS_NAME, LogMessageType.PROCESS, "Processing...")
        commands = self.commandQueue.get_commands()

        #Perform all transactions
        pprint(self.stockExchange.get_sales(commands, self.all_assets)) #TODO
        self.handle_transactions(commands)

        #Deduct time on all commands that need it
        expiring_commands : list[ExpiringCommand] = list(filter(lambda a : issubclass(type(a), ExpiringCommand), commands))
        for expiring_command in expiring_commands:
            try:
                has_expired = self.commandQueue.deduct_time(expiring_command)
                if (has_expired):
                    if (isinstance(expiring_command, BuyCommand)):
                        #Return amount in escrow
                        self.bank.transfer_from_escrow(expiring_command.user, expiring_command.max_price)
                        self.messageManager.send_message_queued(expiring_command.user, expiring_command, MessageType.INFO, "BUY operation expired. :marseylaugh:")
                        self.log.add_log_message(self.CLASS_NAME, LogMessageType.EXPIRED, f"Refunding {expiring_command.max_price}", user = expiring_command.user)
                    elif (isinstance(expiring_command, SellCommand)):
                        #Return asset in escrow
                        self.bank.transfer_asset_from_escrow(expiring_command.user, expiring_command.asset, 1)
                        self.messageManager.send_message_queued(expiring_command.user, expiring_command, MessageType.INFO, "SELL operation expired. :marseylaugh:")
                        self.log.add_log_message(self.CLASS_NAME, LogMessageType.EXPIRED, f"Refunding 1 {expiring_command.asset.name}", user = expiring_command.user)
            except BaseException as e:
                self.database.rollback()
                print(f"=====Exception occurred!=====")
                print("While attempting to make a command expire:")
                pprint(expiring_command)
                print(f"We got: \"{e}\"")
                print(traceback.format_exc())
                self.log.add_log_message(self.CLASS_NAME, LogMessageType.EXCEPTION, str(traceback.format_exc()))
            else:
                self.database.commit()

        for queued_message in self.messageManager.get_all_queued_messages():
            try:
                user : User = queued_message['user']
                message : str = queued_message['message']
                self.api.send_message(user.name, message)
            except BaseException as e:
                print(f"=====Exception occurred!=====")
                print("While processing sending digest:")
                pprint(queued_message)
                print(f"We got: \"{e}\"")
                print(traceback.format_exc())
                self.log.add_log_message(self.CLASS_NAME, LogMessageType.EXCEPTION, str(traceback.format_exc()))
        
        #Increment time
        current_time = self.database.get_current_time_id()
        self.database.set_current_time_id(current_time+1)
        self.database.commit()

    def handle_transactions(self, commands: list[Command]):
        sales = self.stockExchange.get_sales(commands, [Asset(1, "PUTIN"), Asset(2, "ANTIFA")])

        for asset, asset_sales in sales.items():
            self.log.add_log_message(self.CLASS_NAME, LogMessageType.PROCESS, f"Processing {asset.name}...")
            for completed_sale in asset_sales['completed_sales']:
                try:
                    if (asset_sales['buyers_market']):
                        market_explanation = "Buyer's Market. Buyer pays seller's listed price."
                    else:
                        market_explanation = "Seller's Marker. Buyer pays buyer's max price."

                    sale_price :int = completed_sale['sale_price']
                    buy_offer : BuyCommand = completed_sale['buy_command']
                    sell_offer : SellCommand = completed_sale['sell_command']
                    buyer = buy_offer.user
                    seller = sell_offer.user
                    buyer_max_price = buy_offer.max_price

                    self.log.add_log_message(self.CLASS_NAME, LogMessageType.COMPLETED_SALE, f"{seller.name} sold {buyer.name} a share of {asset.name} for {sale_price} in a {market_explanation} Sell Offer = {sell_offer}, Buy Offer = {buy_offer}")

                    self.bank.sell_asset(buyer, seller, asset, sale_price, buyer_max_price)
                    self.messageManager.send_message_queued(seller, sell_offer, MessageType.SUCCESS, f"Sold ${asset.name} for {sale_price}. ({market_explanation})")
                    self.messageManager.send_message_queued(buyer, buy_offer, MessageType.SUCCESS, f"Bought ${asset.name} for {sale_price}. ({market_explanation})")
                    self.commandQueue.delete_command(sell_offer)
                    self.commandQueue.delete_command(buy_offer)
                except AssertionError as assertionError:
                    buy_offer : BuyCommand = completed_sale['buy_command']
                    sell_offer : SellCommand = completed_sale['sell_command']
                    buyer = buy_offer.user
                    seller = sell_offer.user
                    self.messageManager.send_message_queued(seller, sell_offer, MessageType.ERROR, f"Jewish tricks detected! The Jewish Trick was: {assertionError}. If you weren't the Jew, it was probably @{buyer.name}. ✡")
                    self.messageManager.send_message_queued(buyer, buy_offer, MessageType.ERROR, f"Jewish tricks detected! The Jewish Trick was: {assertionError}. If you weren't the Jew, it was probably @{seller.name}. ✡")
                    
                    self.log.add_log_message(self.CLASS_NAME, LogMessageType.JEWRY, f"Jewish trick. buy offer = {buy_offer}, sell offer = {sell_offer}, buyer = {buyer.name}, seller = {seller.name}, exception = {assertionError}")
                    print(f"WARNING: Jewish trick detected {assertionError}")
                    self.database.rollback()
                except BaseException as baseException:
                    self.database.rollback()
                    print(f"=====Exception occurred!=====")
                    print("While processing this sale:")
                    pprint(completed_sale)
                    print(f"We got: \"{baseException}\"")
                    print(traceback.format_exc())
                    self.log.add_log_message(self.CLASS_NAME, LogMessageType.EXCEPTION, str(traceback.format_exc()))
                else:
                    self.database.commit()

            for outbidded_buy_command in asset_sales['failed_sales']['outbidded']:
                self.messageManager.send_message_queued(outbidded_buy_command.user, outbidded_buy_command, MessageType.INFO, "You were outbidded. Consider increasing your max price.")
                self.log.add_log_message(self.CLASS_NAME, LogMessageType.FAILED_SALE, f"OUTBIDDED - {outbidded_buy_command}", user = outbidded_buy_command.user)
            for outpriced_sell_command in asset_sales['failed_sales']['outpriced']:
                self.messageManager.send_message_queued(outpriced_sell_command.user, outpriced_sell_command, MessageType.INFO, "You were outpriced. Consider decreasing the listed price of the asset.")
                self.log.add_log_message(self.CLASS_NAME, LogMessageType.FAILED_SALE, f"OUTPRICED - {outpriced_sell_command}", user = outpriced_sell_command.user)
            for no_sellers_buy_command in asset_sales['failed_sales']['no_sellers']:
                self.messageManager.send_message_queued(no_sellers_buy_command.user, no_sellers_buy_command, MessageType.INFO, "Dead market. It seems no-one is selling. Consider shilling about how the asset will crash soon.")
                self.log.add_log_message(self.CLASS_NAME, LogMessageType.FAILED_SALE, f"DEAD MARKET - {no_sellers_buy_command}", user = no_sellers_buy_command.user)
            for no_buyers_sell_command in asset_sales['failed_sales']['no_buyers']:
                self.messageManager.send_message_queued(no_buyers_sell_command.user, no_buyers_sell_command, MessageType.INFO, "Dead market. It seems no-one is buying. Consider shilling about how the asset will go to the 🌛 soon.")
                self.log.add_log_message(self.CLASS_NAME, LogMessageType.FAILED_SALE, f"DEAD MARKET - {no_buyers_sell_command}", user = no_buyers_sell_command.user)
            for stingy_buy_command in asset_sales['failed_sales']['stingy']:
                self.messageManager.send_message_queued(stingy_buy_command.user, stingy_buy_command, MessageType.WARNING, f"It was a buyer's market, and the price was still too high for you. Learn how the market works, retard.")
                self.log.add_log_message(self.CLASS_NAME, LogMessageType.FAILED_SALE, f"STINGY - {stingy_buy_command}", user = stingy_buy_command.user)

            try:
                if (not asset_sales['dead_market']):
                    sale_prices = [i['sale_price'] for i in asset_sales['completed_sales']]
                    self.priceTracker.set_price(asset, average(sale_prices))
                else:
                    self.priceTracker.maintain_price(asset)
            except BaseException as e:
                self.database.rollback()
                print(f"=====Exception occurred!=====")
                print(f"While setting the pricepoint for {asset.name}:")
                pprint(asset_sales)
                print(f"We got: \"{e}\"")
                print(traceback.format_exc())
                self.log.add_log_message(self.CLASS_NAME, LogMessageType.EXCEPTION, str(traceback.format_exc()))
            else:
                self.database.commit()

    def ipo(self, stock_name : str, amount : int, asking_price : int):
        self.database.add_asset(stock_name.upper())
        hmse_user = User(0, "HMSE")
        self.database.add_or_update_user(hmse_user)
        asset = self.database.get_asset_with_name(stock_name.upper())
        self.database.set_owned_assets_in_escrow(hmse_user, asset, amount)
        for i in range(amount):
            self.commandQueue.add_command(SellCommand(None, 100, hmse_user, asset, asking_price))
        self.database.commit()


with open("token", "r") as file:
    real_auth_token = file.read()


if (TEST):
    endpoint = "localhost"
    auth_token = TEST_AUTH_TOKEN
    database_filename = "test_db.db"
    log_filename = "test_log.db"
else:
    endpoint = "rdrama.net"
    auth_token = real_auth_token
    database_filename = "hmse.db"
    log_filename = "log.db"

api = RDramaAPIInterface(auth_token, endpoint, TEST)
database = Database(database_filename)
log = Log(log_filename, database)
bank = Bank(database, log)
parser = Parser()
commandQueue = CommandQueue(database)

hmse = HMSE(api, database, bank, parser, commandQueue, log)

if (sys.argv[1] == 'update'):
    hmse.update()
elif (sys.argv[1] == 'process'):
    hmse.process()
elif (sys.argv[1] == 'ipo'):
    stock_name = sys.argv[2]
    amount = int(sys.argv[3])
    asking_price = int(sys.argv[4])
    hmse.ipo(stock_name, amount, asking_price)
else:
    print("lol. lmao.")

database.close()
log.close()