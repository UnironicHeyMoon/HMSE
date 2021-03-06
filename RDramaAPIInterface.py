import time
from urllib import response
from xmlrpc.client import boolean
import bs4
import requests
import pprint
from bs4 import BeautifulSoup, Tag
from ast import literal_eval

RETRIEVE_COMMENT_REPLIES = True
COMMENT_BASE_CLASS = "anchor comment"
USER_INFO_CLASS = "user-info"
COMMENT_TEXT_CLASS = 'comment-text mb-0'

'''
Wrapper around the RDRama API
'''
class RDramaAPIInterface:
    def __init__(self, authorization_token, site, test_mode : bool, sleep : float) -> None:
        self.headers={"Authorization": authorization_token}
        self.site = site
        self.welcome_message = "Welcome to " if test_mode else "We're always adding new features, and we take a fun-first approach to development."
        self.sleep = sleep

    '''
    Sends a message to a user.
    '''
    def send_message(self, username, message):
        if (username == "HMSE"):
            return
        url=f"https://{self.site}/@{username}/message"
        return self.post(url, data={'message':message})

    '''
    Replies to the comment with the given id.
    '''
    def reply_to_comment(self,parent_fullname, parent_submission, message):
        url=f"https://{self.site}/comment"
        return self.post(url, data={
            'parent_fullname':parent_fullname,
            'submission': parent_submission,
            "body": message
            })

    '''
    Replies to the comment with the given id.
    '''
    def reply_to_comment_easy(self,comment_id, parent_submission, message):
        return self.reply_to_comment(f"t3_{comment_id}", parent_submission, message)

    '''
    Gets "all" comments. TODO: Probably need to add pagination support if I want to actually use this
    '''
    def get_comments(self):
        url=f"https://{self.site}/comments"
        return self.get(url)

    '''
    Calls the notifications endpoint
    '''
    def get_notifications(self, page : int):
        url=f"https://{self.site}/notifications?page={page}"
        return self.get(url)

    '''
    Given a notification, returns whether or not the message is from Drama (ie, the messenger)
    '''
    def is_message_from_drama(self,notification) -> bool:
        return notification['author_name'] == "Drama"

    '''
    IMPLYING THAT THE MESSAGE IS FROM DRAMA, determines whether or not the notification is a gift transaction.
    '''
    def is_message_is_a_gift_transaction(self,notification) -> bool:
            soup = BeautifulSoup(notification['body_html'], 'html.parser')
                
            p = soup.html.body.p
            #The first element is :marseycapitalistmanlet:. If not, we know this isn't a gift
            marsey_capitalist_manlet = p.contents[0]
            return (marsey_capitalist_manlet.name == "img" and marsey_capitalist_manlet['alt'] == ":marseycapitalistmanlet:")        


    '''
    Whether or not the message is a follow notification.
    '''
    def is_message_a_follow_notification(self, notification):
        return "has followed you!" in notification['body_html']
    
    '''
    Whether or not the message is an unfollow notification.
    '''
    def is_message_an_unfollow_notification(self, notification):
        return "has unfollowed you!" in notification['body_html']

    '''
    Parses a gift transaction
    '''
    def parse_gift_transaction(self, notification):
        soup = BeautifulSoup(notification['body_html'], 'html.parser')
                
        p = soup.html.body.p

        #The third element is the username. It is a hyperlink tag containing the name of the user
        user_element = p.contents[2]
        user_id = user_element['href'].split("/")[2] #the hyperlink is formatted like so: /id/x, where x is the id
        user_name = user_element.img.string[1:] #the username is within the image tag. we remove the first character, which is an @

        #the fourth element is the "gift" string. It looks like this " has gifted you x coins".
        amount_string = p.contents[3]
        amount = amount_string.string.split(" ")[4]

        return {
            "type": "transfer",
            "user_name": user_name,
            "user_id": int(user_id),
            "amount": int(amount),
            "id": notification['id']
        }

    '''
    parses a post mention
    '''
    def parse_post_mention(self, notification):
        soup = BeautifulSoup(notification['body_html'], 'html.parser')
                
        p = soup.html.body.p

        #The first element is the username. It is a hyperlink tag containing the name of the user
        user_element = p.contents[0]
        user_id = user_element['href'].split("/")[2] #the hyperlink is formatted like so: /id/x, where x is the id
        user_name = user_element.contents[1].string[1:] #the username is after the img tag. we remove the first character, which is an @

        post_element = p.contents[-1]
        post_id = post_element['href'].split("/")[2]
        post_name = post_element.string

        return {
            "type": "post_mention",
            "user_name": user_name,
            "user_id": int(user_id),
            "id": notification['id'],
            "post_name": post_name,
            "post_id": post_id
        }

    '''
    parses a follow notification
    '''
    def parse_follow_notification(self, notification):
        soup = BeautifulSoup(notification['body_html'], 'html.parser')
                
        p = soup.html.body.p

        #The first element is the username. It is a hyperlink tag containing the name of the user
        user_element = p.contents[0]
        user_id = user_element['href'].split("/")[2] #the hyperlink is formatted like so: /id/x, where x is the id
        user_name = user_element.contents[1].string[1:] #the username is after the img tag. we remove the first character, which is an @


        return {
            "type": "follow",
            "user_name": user_name,
            "user_id": int(user_id),
            "id": notification['id']
        }

    '''
    parses an unfollow notification
    '''
    def parse_unfollow_notification(self, notification):
        soup = BeautifulSoup(notification['body_html'], 'html.parser')
                
        p = soup.html.body.p

        #The first element is the username. It is a hyperlink tag containing the name of the user
        user_element = p.contents[0]
        user_id = user_element['href'].split("/")[2] #the hyperlink is formatted like so: /id/x, where x is the id
        user_name = user_element.contents[1].string[1:] #the username is after the img tag. we remove the first character, which is an @

        return {
            "type": "unfollow",
            "user_name": user_name,
            "user_id": int(user_id),
            "id": notification['id']
        }

    '''
    parses a dm
    '''
    def parse_direct_message(self, notification):
        return {
            "type": "direct_message",
            "user_name": notification['author_name'],
            "user_id": notification['author']['id'],
            "id": notification['id'],
            "message_html": BeautifulSoup(notification['body_html'], 'html.parser').html.body.p.text
        }

    '''
    parses a reply to a comment.
    '''
    def parse_comment_reply(self, notification, last_processed_notification_id):
        replies = self.comment_reply_retriever(notification['id'])
        new_replies = []
        
        greatest_reply_id = 0
        for i in replies:
            greatest_reply_id = max(greatest_reply_id, int(i['id']))
            if (i['user_name'] != 'HMSE' and int(i['id']) > last_processed_notification_id):
                new_replies.append(i)

        return {
            "type": "comment_reply",
            "parent_id": notification["id"],
            "id": greatest_reply_id,
            "replies": new_replies,
            "post_name": notification["post"]["title"],
            "post_id": notification["post"]["id"]
        }

    def parse_comment_mention(self, notification, last_processed_notification_id):
        if (notification['id'] <= last_processed_notification_id):
            comment_mention_as_comment_reply = self.parse_comment_reply(notification, last_processed_notification_id)
            if (comment_mention_as_comment_reply['replies'] != []):
                return comment_mention_as_comment_reply
        return {
            "type": "comment_mention",
            "user_name": notification['author_name'],
            "user_id": notification['author']['id'],
            "id": notification["id"],
            "message": notification['body'],
            "post_id": notification['post']['id'],
            "post_name": notification['post']['title']
        }

    '''
    Returns a list of notifications in an easy to process list.
    '''
    def get_parsed_notification(self, last_processed_notification_id, page = 1):
        to_return = []
        did_parse_all = False #Whether or not we need to parse more pages
        has_encountered_welcome = False
        notifications = self.get_notifications(page).json()['data']
        if (notifications == []):
            return []
        for notification in notifications:
            parsed_notification = {}
            did_parse = True
            if self.is_message_from_drama(notification):
                if (self.is_message_is_a_gift_transaction(notification)):
                    parsed_notification = self.parse_gift_transaction(notification)
                elif ("has mentioned you: " in notification['body_html']):
                    parsed_notification = self.parse_post_mention(notification)
                elif (self.is_message_a_follow_notification(notification)):
                    parsed_notification = self.parse_follow_notification(notification)
                elif (self.is_message_an_unfollow_notification(notification)):
                    parsed_notification = self.parse_unfollow_notification(notification)
                elif (self.welcome_message in notification['body_html']):
                    #Welcome message
                    did_parse = False
                    has_encountered_welcome = True
                elif ("if you don't know what to do next" in notification['body_html']):
                    #API approval message
                    did_parse = False
                else:
                    did_parse = False
            elif notification['post'] == '':
                #Direct message
                parsed_notification = self.parse_direct_message(notification)
            elif notification['author_name'] == "HMSE":
                #comment reply
                parsed_notification = self.parse_comment_reply(notification, last_processed_notification_id)
            else:
                #comment mention
                parsed_notification = self.parse_comment_mention(notification, last_processed_notification_id)
            
            if (did_parse):
                should_stop_not_comment_reply = parsed_notification['id'] <= last_processed_notification_id and parsed_notification['type'] != "comment_reply"
                should_stop_comment_reply = parsed_notification['type'] == 'comment_reply' and parsed_notification['replies'] == []
                if (should_stop_not_comment_reply):
                    #We are done.
                    did_parse_all = True
                    break
                else:
                    to_return.append(parsed_notification)
        
        if (not did_parse_all and not has_encountered_welcome):
            to_return.extend(self.get_parsed_notification(last_processed_notification_id, page+1))
        return to_return

    def reply_to_direct_message(self, message_id : int, message : str):
        url=f"https://{self.site}/reply"
        return self.post(url, data = {
            'parent_id' : message_id,
            'body': message
        }, allowed_failures=[500]) #There is a bug (probably) with the site that causes 500 errors to be sent when doing this via json. TODO: Ask Aevann why

    def get_comment(self, id):
        url=f"https://{self.site}/comment/{id}"
        return self.get(url)

    '''
    I have no clue what this is supposed to do, lol.
    '''
    def clear_notifications(self):
        url=f"https://{self.site}/clear"
        return self.post(url, headers=self.headers)

    def give_coins(self, user, amount):
        url=f"https://{self.site}/@{user}/transfer_coins"
        return self.post(url, data={'amount':amount})

    def get(self, url, allowed_failures = []):
        time.sleep(self.sleep)
        response = requests.get(url, headers=self.headers)
        if (response.status_code != 200 and response.status_code not in allowed_failures):
            raise BaseException(f"GET {url} ({response.status_code}) {response.json()}")
        else:
            return response
    
    def post(self, url, data, allowed_failures = []):
        time.sleep(self.sleep)
        response = requests.post(url, headers=self.headers, data=data)
        if (response.status_code != 200  and response.status_code not in allowed_failures):
            raise BaseException(f"POST {url} ({response.status_code}) {data} => {response.json()}")
        else:
            return response

    '''
    Performs scraping of all comment replies.
    This is super finicky... and I am also worried that it will cause throttling.
    So it should be easily disabled.
    '''
    def comment_reply_retriever(self, id):
        if (not RETRIEVE_COMMENT_REPLIES):
            return []
        url = f"https://{self.site}/comment/{id}#context"
        headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
        }
        result = requests.get(url, headers=headers).text
        soup = BeautifulSoup(result, "html.parser")
        all_comments = soup.find_all("div", {"class":COMMENT_BASE_CLASS})
        to_return = []
        for comment in all_comments:
            comment_id = comment['id'].split("-")[1]
            user_info_div = comment.find("div", {'class':USER_INFO_CLASS})
            user_info = literal_eval(user_info_div.a['onclick'][9:-1])
            user_name = user_info['username']
            user_id = user_info['id']
            comment_text_div = comment.find("div", {'class':COMMENT_TEXT_CLASS})
            message = comment_text_div.p.text
            to_return.append({
                'id': comment_id,
                'user_name': user_name,
                'user_id': user_id,
                'message': message
            })
        return to_return




#TODO: Move this to a separate file
TEST_AUTH_TOKEN = "6vRGm_VsgHlzywNUeJGJulOCv87cAJd4gBlSXxi-VU3zFbLPI-pd29k1QKUke1K-Nrjs2Ieg_buNl6evMG07XRH1qf1qSw5t-VRjNbXkyzlHwufZYNm6z9pygrOcNZq8"
if __name__ == "__main__":
    rdrama = RDramaAPIInterface(TEST_AUTH_TOKEN, "localhost")
    print(rdrama.get_parsed_notification(104))