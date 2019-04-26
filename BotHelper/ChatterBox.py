import re
import random
from enum import Enum
from slackclient import SlackClient

class ChatterType(Enum):
    """Create an enum structure for delineating various types of chatter"""
    THANKS = 1

class ChatterBox:
    """Create an object with methods designed to interact with various types of user chatter
    
        Attributes:
        
        bot_id: string comprised of the current bot_id in use.
        bot_text: string in the form "<@bot_id>". Used to identify mentions.
        bot_start_texts: list containing the various concatenated forms of bot_text + command, such that "command"
            is a valid bot command.
        thanks_regex: a regular expression designed to determine if the user is thanking the bot.
        slack_client: an instance of slackclient utilizing the standard slack bot token.
        oauth_client: an instance of slackclient utilizing the oauth slack token.
        commands_list: list of valid bot commands imported from main().
        thanks_messages: dictionary of various you're welcome responses for the bot.    
    """

    def __init__(self):
        """Initialize many of our attritutes here."""
        self.bot_id = None
        self.bot_text = None
        self.bot_start_texts = None
        self.thanks_regex = None
        self.slack_client = None
        self.oauth_client = None
        self.commands_list = None
        self.thanks_messages = {
            "No Thanks" : ["Did I help you with something? I don't recall.", "For what?  I don't remember", "I don't see that I helped you.  Try a command!"],
            "One Thanks" : ["You're welcome, ", "Of course, ", "No, thank YOU, ", "No problem, ", "Anytime, ",
                                "My pleasure, ", "I live to serve, ", "Don't mention it, ", "Happy to help, ", "De nada, ", "No worries, "],
            "Two Thanks" : ["Thanking me twice?  I feel special, ", "No need to keep thanking me, ", "You're welcome x2, "],
            "Three Thanks" : ["You're welcome.  You can stop now, ", "Again huh?  Sure thing, ", "That is probably adequate thanking, "],
            "Four Thanks" : ["Seriously, stop thanking me, ", "I think that is good enough, ", "You're welcome.  Again.  You can stop now, "]
        }

    def set_things(self, bot_id, slack_client, oauth_client, commands):
        """Set the attributes that required outside information.

            Params:

            bot_id: the correct bot id from main().  Used to set bot_id, bot_text, and thanks_regex.
            slack_client: the correct slack_client from main().  Used to set slack_client.
            oauth_client: the correct oauth_client from main().  Used to set oauth_client.
            commands: the list of commands from main().
        
        """
        self.bot_id = bot_id
        self.bot_text = "<@{}>".format(bot_id)
        self.commands_list = commands
        self.bot_start_texts = [self.bot_text + " " + x for x in self.commands_list]
        self.thanks_regex = r"^.*((([Tt][Hh][Aa][Nn][Kk][Ss]?(\s[Yy][Oo][Uu])?)[\w\s,.!]*(?=\s?<@" + self.bot_id + r">))|(<@" \
                + self.bot_id + r">(?=[,.!]*\s[,.!]*([Tt][Hh][Aa][Nn][Kk][Ss]?(\s[Yy][Oo][Uu])?)))).*$"
        self.slack_client = slack_client
        self.oauth_client = oauth_client
        
    
    def is_chatter(self, event):
        """Determine if the event in question is user chatter.  Return True/False and an appropriate chatter type.
        
            Params:

            event: the event to process

            Possible Issues:

            This function will throw a KeyError exception in the case that event does not have a "text" key.         
        """
        # The first thing to look for is a thank you message:

        if re.match(self.thanks_regex, event["text"]):
            return True, ChatterType.THANKS
        else:
            return False, None

    def process_chatter(self, event, type):
        """Process the requested event as user chatter.

            Params:

            event: the event to be processed.
            type: ChatterType indicating the route to send the event on.    
        """
        # Check to see the chatter type here:

        if type == ChatterType.THANKS:
            self.was_thanked(event)

    def was_thanked(self, event):
        """Give an appropriate response to the user if he/she thanks the bot.
        
            Params:

            event: the event in which a user is thanking the bot.
        """

        # Grab some stuff from the event.  The channel where the message was, the user
        # who did the thanking, and the timestamp
        thanked_channel = event["channel"]
        thanked_user = event["user"]
        thanked_time = event["ts"]

        # This function posts a response to the user depending on a few circumstances to be figured out
        # shortly
        def say_youre_welcome(num, message_pool):
            
            if num <= 4:
                # Say something to the user
                self.slack_client.api_call(
                    "chat.postMessage",
                    channel=thanked_channel,
                    text=random.choice(message_pool) + "<@{}>.".format(thanked_user)
                )

                if num == 1:
                    # Give a nice reaction to the users message
                    self.slack_client.api_call(
                        "reactions.add",
                        channel=thanked_channel,
                        name="thumbsup",
                        timestamp=thanked_time
                    )
                elif num == 2:
                    # Give a nice reaction to the users message
                    self.slack_client.api_call(
                        "reactions.add",
                        channel=thanked_channel,
                        name="astonished",
                        timestamp=thanked_time
                    )
            else:
                self.oauth_client.api_call(
                    "chat.update",
                    channel=thanked_channel,
                    text="_This thank you has been redacted._",
                    ts=thanked_time
                )

        # Grab the chat history here
        chat_history = self.oauth_client.api_call(
                        "channels.history",
                        channel=thanked_channel,
                        latest=thanked_time,
                        count=20
                        )["messages"]
        
        # Empty histories for specific user
        user_history = []
        user_bot_history = []
        user_thanks_history = []

        # Step One: See if the user actually had a bot request in the last 10 messages
        # in the channel:

        for item in chat_history:
            if "subtype" not in item:
                user_history.append(item["text"])

        for item in user_history:
            if item.startswith(tuple(self.bot_start_texts)):
                user_bot_history.append(item)
            if re.match(self.thanks_regex, item):
                user_thanks_history.append(item)
        
        if len(user_thanks_history) == 0:
            say_youre_welcome(0, self.thanks_messages["No Thanks"])
        elif len(user_thanks_history) == 1:
            say_youre_welcome(1, self.thanks_messages["One Thanks"])
        elif len(user_thanks_history) == 2:
            say_youre_welcome(2, self.thanks_messages["Two Thanks"])
        elif len(user_thanks_history) == 3:
            say_youre_welcome(3, self.thanks_messages["Three Thanks"])
        elif len(user_thanks_history) == 4:
            say_youre_welcome(4, self.thanks_messages["Four Thanks"])
        elif len(user_thanks_history) >= 5:
            say_youre_welcome(5, None)