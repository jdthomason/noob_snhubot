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

        Functions:

        set_things: many of the attributes cannot be set immediately.  This is called when we can create the werid ones.
        is_chatter: function used to determine if a user message is "chatter."
        process_chatter: if a message is deemed "chatter," it can be processed here.
        was_thanked: if the user is thanking the bot, we will handle the next step here.
    """

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
        self.thanks_regex = re.compile(
            r"""
            # match anything, but stop at the action
            ^.*?
            # start of main non-capture group    
            (?:
            # option 1: bot followed by thanks  
            (?:<@{0}>[\W\w]*?\sthanks?(?:\syou)?)
            # or:
            |
            # option 2: thanks followed by bot
            (?:thanks?(?:\syou)?[\W\w]*?\s<@{0}>)
            # end of main non-capture group
            )       
            # match anything, but stop at the end of the line
            .*?$     
            """.format(self.bot_id),
            re.IGNORECASE | re.VERBOSE
        )
        self.slack_client = slack_client
        self.oauth_client = oauth_client
        self.thanks_messages = [
            ["Did I help you with something? I don't recall, ", "For what?  I don't remember, ", "I don't see that I helped you.  Try a fun command, "],
            ["You're welcome, ", "Of course, ", "No, thank YOU, ", "No problem, ", "Anytime, ","My pleasure, ", "I live to serve, ", "Don't mention it, ",
                "Happy to help, ", "De nada, ", "No worries, "],
            ["Thanking me twice?  I feel special, ", "No need to keep thanking me, ", "You're welcome x2, "],
            ["You're welcome.  You can stop now, ", "Again huh?  Sure thing, ", "That is probably adequate thanking, "],
            ["Seriously, stop thanking me, ", "I think that is good enough, ", "You're welcome.  Again.  You can stop now, "]
        ]
        
    
    def is_chatter(self, event):
        """Determine if the event in question is user chatter.  Return True/False and an appropriate chatter type.
        
            Params:

            event: the event to process

            Possible Issues:

            This function will throw a KeyError exception in the case that event does not have a "text" key.         
        """
        # The first thing to look for is a thank you message:

        if self.thanks_regex.match(event["text"]):
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
        def say_youre_welcome(bot_history, thanks_history):
            
            def youre_welcome_message(message_pool):
                # Say something to the user
                self.slack_client.api_call(
                    "chat.postMessage",
                    channel=thanked_channel,
                    text=random.choice(message_pool) + "<@{}>.".format(thanked_user)
                )

            def youre_welcome_emote(icon):
                # Give a nice reaction to the users message
                self.slack_client.api_call(
                    "reactions.add",
                    channel=thanked_channel,
                    name=icon,
                    timestamp=thanked_time
                )

            ### TODO: The user can quickly hit the thank you cap if he/she had thanked the bot before actually issuing a command.
            ### Probably need some more logic to keep that from occurring.
            if bot_history == 0:
                youre_welcome_message(self.thanks_messages[0])
                youre_welcome_emote("question")
            else:
                if thanks_history == 0:
                    youre_welcome_message(self.thanks_messages[1])
                    youre_welcome_emote("thumbsup")
                elif thanks_history == 1:
                    youre_welcome_message(self.thanks_messages[2])
                    youre_welcome_emote("astonished")
                elif thanks_history == 2:
                    youre_welcome_message(self.thanks_messages[3])
                elif thanks_history == 3:
                    youre_welcome_message(self.thanks_messages[4])
                elif thanks_history >= 4:
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

        # Step One: See if the user actually had a bot request in the last 20 messages
        # in the channel:

        # This pulls all the messages from the user
        for item in chat_history:
            if "subtype" not in item:
                user_history.append(item["text"])

        # Process the items
        for item in user_history:
            # This separates the messages with bot commands
            if item.startswith(tuple(self.bot_start_texts)):
                user_bot_history.append(item)
            # This separates the messages with previous thanks
            if self.thanks_regex.match(item):
                user_thanks_history.append(item)

        # Do the work
        say_youre_welcome(len(user_bot_history), len(user_thanks_history))