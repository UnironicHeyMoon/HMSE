from asyncio import to_thread
import random
from Asset import Asset
from Command import Command
from RDramaAPIInterface import RDramaAPIInterface
from Randsey import Randsey
from User import User

class MessageManager:
    def __init__(self, api : RDramaAPIInterface, randsey : Randsey) -> None:
        self.api = api
        self.unsent_messages = {}
        self.randsey = randsey

    def send_message(self, receiver: User, message : str):
        self.api.send_message(receiver.name, message)
        pass
    
    def send_message_queued(self, user: User, command : Command, message_type : int, message : str):
        if (user.id not in self.unsent_messages):
            self.unsent_messages[user.id] = []
        self.unsent_messages[user.id].append({
            'user': user,
            'command': command,
            'message_type': message_type,
            'message': message
        })
    
    def get_all_queued_messages(self):
        to_return = []
        for user_id, messages in self.unsent_messages.items():
            message = "# Hourly Trade Notifications\n\n"
            message += "Please see the following notifications about your placed commands!\n\n"
            message += self.construct_digest_message_table(messages)
            message += "\n\n"
            message += "Thanks,\n\n"
            message += "HMSE\n\n"
            message += self.randsey.get_randsey_says(messages[0]['user'])
            user = messages[0]['user']
            to_return.append({
                "user": user,
                "message": message
            })
        return to_return

    def construct_digest_message_table(self, messages : list[dict]):
        to_return = "<table style=\"border: 1px solid black;border-collapse: collapse;\">"
        #Header
        to_return += "<thead style=\"border: 1px solid black;border-collapse: collapse;\">"
        to_return += "<tr>"
        to_return += "<td style=\"border: 1px solid black;border-collapse: collapse;\">Info</td>"
        to_return += "<td style=\"border: 1px solid black;border-collapse: collapse;\">ID</td>"
        to_return += "<td style=\"border: 1px solid black;border-collapse: collapse;\">Command</td>"
        to_return += "<td style=\"border: 1px solid black;border-collapse: collapse;\">Message</td>"
        to_return += "</tr>"
        to_return += "</thead>"
        #Body
        to_return += "<tbody>"
        for message in messages:
            to_return += "<tr>"
            to_return += f"<td style=\"border: 1px solid black;border-collapse: collapse;\">{self.get_message_type_symbol(message['message_type'])}</td>" #Message Type Symbol
            to_return += f"<td style=\"border: 1px solid black;border-collapse: collapse;\">{message['command'].id}</td>" #ID
            to_return += f"<td style=\"border: 1px solid black;border-collapse: collapse;\">{message['command'].user_friendly_description}</td>" #Description
            to_return += f"<td style=\"border: 1px solid black;border-collapse: collapse;\">{message['message']}</td>" #Message
            to_return += "</tr>"
        to_return += "</tbody>"
        to_return += "</table>"
        return to_return

    def get_message_type_symbol(self, message_type : int):
        if (message_type == MessageType.SUCCESS):
            return "✅"
        elif (message_type == MessageType.ERROR):
            return "❌"
        elif (message_type == MessageType.WARNING):
            return "⚠"
        elif (message_type == MessageType.INFO):
            return "ℹ"
        else:
            return "?"

class MessageType:
    SUCCESS = 3
    ERROR = 2
    WARNING = 1
    INFO = 0