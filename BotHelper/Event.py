import re


class Event:
    """
    This is the class for individual event objects
    """

    def __init__(self):
        """
        Initial values
        """
        self.new_users = False
        self.users_to_add = []
        self.is_mention = False
        self.is_reaction = False
        self.mentioned_users = None
        self.num_mentions = None
        self.user_id = None
        self.event_text = None
        self.reacted_to_user = None
        self.emojis_used = None
        self.words = None
        self.images = None
        self.snippets = None
        self.files = None
        self.data = None
        self.bot_calls = None

    def set_starting_values(self, event, users, bot_id):

        # first thing, get the user id:

        self.user_id = event["user"]

        # then, determine if they're new:

        if {"user_id": self.user_id} not in users:
            self.users_to_add.append(self.user_id)

        # see if the event was a reaction, if not, set the event text and check for mentions:

        if event["type"] == "reaction_added":
            if "item_user" in event:
                self.is_reaction = True
                self.reacted_to_user = event["item_user"]

                if {"user_id": self.reacted_to_user} not in users:
                    self.users_to_add.append(self.reacted_to_user)
        else:
            # set the text:

            self.event_text = event["text"]

            # see if there are any mentions:

            if len(re.findall(r"<@\w{6,12}>", self.event_text)) > 0:
                self.mentioned_users = set()
                for m in re.findall(r"<@\w{6,12}>", self.event_text):
                    if m != "<@{}>".format(self.user_id) and m != "<@{}>".format(bot_id) \
                            and m != "<@USLACKBOT>" and re.search(r"\w+", m)[0] not in self.mentioned_users:
                        self.mentioned_users.add(re.search(r"\w+", m)[0])
                if len(self.mentioned_users) > 0:
                    self.is_mention = True

                    for user in self.mentioned_users:
                        if {"user_id": user} not in users:
                            self.users_to_add.append(user)

        if len(self.users_to_add) > 0:
            self.new_users = True

    def process_message(self, event, bot_id):
        # do the rest of the stuff here
        self.emojis_used = len(re.findall(r":[\w-]+:", self.event_text))
        self.words = len(self.event_text.split(" ")) - self.emojis_used if \
            self.event_text != "" and re.match(r"^(\s*:[\w-]+:\s*)*$", self.event_text) is None else 0
        self.images = 1 if "files" in event and event["files"][0]["mimetype"].startswith("image") else 0
        self.snippets = 1 if "files" in event and event["files"][0]["mimetype"].startswith("text") else 0
        self.files = 1 if "files" in event and not event["files"][0]["mimetype"].startswith("image") \
                          and not event["files"][0]["mimetype"].startswith("text") else 0
        self.data = (float(event["files"][0]["size"]) * 1e-6) if "files" in event \
                                                                     and "size" in event["files"][0] else 0
        self.bot_calls = 1 if self.event_text.startswith("<@{}>".format(bot_id)) else 0
