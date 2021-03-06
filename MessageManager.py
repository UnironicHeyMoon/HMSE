from Command import Command
from Randsey import Randsey
from User import User

'''
Allows for sending multiple messages at once, in a nice, orderly manner
'''
class MessageManager:
    def __init__(self, randsey : Randsey) -> None:
        self.unsent_messages = {}
        self.randsey = randsey
    
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
            message += self.construct_digest_message_table(self.collapse_messages(messages))
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

    def collapse_messages(self, messages : list[dict]):
        collapsed_messages = []
        for message in messages:
            has_collapsed = False
            for collapsed_message in collapsed_messages:
                if collapsed_message['message'] == message['message'] and collapsed_message['command'].user_friendly_description == message['command'].user_friendly_description:
                    has_collapsed = True
                    collapsed_message['count']+=1
                    break
            if (not has_collapsed):
                collapsed_messages.append(
                    {
                        'message': message['message'],
                        'command': message['command'],
                        'message_type': message['message_type'],
                        'count': 1
                    }
                )
        return collapsed_messages

    def construct_digest_message_table(self, messages : list[dict]):
        to_return = "<table style=\"border: 1px solid black;border-collapse: collapse;\">"
        #Header
        to_return += "<thead style=\"border: 1px solid black;border-collapse: collapse;\">"
        to_return += "<tr>"
        to_return += "<td style=\"border: 1px solid black;border-collapse: collapse;\">Info</td>"
        to_return += "<td style=\"border: 1px solid black;border-collapse: collapse;\">Count</td>"
        to_return += "<td style=\"border: 1px solid black;border-collapse: collapse;\">Command</td>"
        to_return += "<td style=\"border: 1px solid black;border-collapse: collapse;\">Message</td>"
        to_return += "</tr>"
        to_return += "</thead>"
        #Body
        to_return += "<tbody>"
        for message in messages:
            to_return += "<tr>"
            to_return += f"<td style=\"border: 1px solid black;border-collapse: collapse;\">{self.get_message_type_symbol(message['message_type'])}</td>" #Message Type Symbol
            to_return += f"<td style=\"border: 1px solid black;border-collapse: collapse;\">{message['count']}</td>" #ID
            to_return += f"<td style=\"border: 1px solid black;border-collapse: collapse;\">{message['command'].user_friendly_description}</td>" #Description
            to_return += f"<td style=\"border: 1px solid black;border-collapse: collapse;\">{message['message']}</td>" #Message
            to_return += "</tr>"
        to_return += "</tbody>"
        to_return += "</table>"
        return to_return

    def get_message_type_symbol(self, message_type : int):
        if (message_type == MessageType.SUCCESS):
            return "???"
        elif (message_type == MessageType.ERROR):
            return "???"
        elif (message_type == MessageType.WARNING):
            return "???"
        elif (message_type == MessageType.INFO):
            return "???"
        else:
            return "?"

class MessageType:
    SUCCESS = 3
    ERROR = 2
    WARNING = 1
    INFO = 0