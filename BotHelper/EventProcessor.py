from datetime import datetime
from threading import Thread
from time import sleep
from .Event import Event
from .MongoConnection import MongoConnection


class EventProcessor:
    """
    Hopefully, this will act as a watcher object to watch Slack events.
    """

    def __init__(self, slack_client, config):
        self.slack_client = slack_client
        self.DB_CONFIG = config
        self.mongo = MongoConnection(
            db=self.DB_CONFIG['db'],
            collection=self.DB_CONFIG['collections']['leaderboard'],
            hostname=self.DB_CONFIG['hostname'],
            port=self.DB_CONFIG['port']
        )
        self.events = []
        self.allowed_events = ["message", "reaction_added"]
        self.bot_id = None

    def run(self):
        t = Thread(target=self.process_events)
        t.daemon = True
        t.start()

    def set_bot_id(self, id):
        self.bot_id = id

    def process_events(self):

        # Yes events:
        # message, reaction_added

        while True:
            if len(self.events) == 0:
                sleep(1)
            else:
                while len(self.events) > 0:

                    current_event = Event()
                    current_event.set_starting_values(self.events[0],
                                                 self.mongo.find_documents({}, {"_id": 0, "user_id": 1}),
                                                 self.bot_id)

                    # first, figure out if the user is new to the db:

                    if current_event.new_users:
                        for u in current_event.users_to_add:
                            user_info = self.slack_client.api_call("users.info", user=u)
                            if "error" not in user_info:
                                real_name = user_info['user']['real_name']
                                display_name = user_info['user']['profile']['display_name']
                                self.write_user_shell(u, real_name, display_name)
                            else:
                                # bot users produce errors on this API call
                                # remove from mentions
                                current_event.mentioned_users.remove(u)

                    if current_event.is_reaction:
                        self.write_user_reactions(current_event.user_id, current_event.reacted_to_user)
                    else:
                        current_event.process_message(self.events[0], self.bot_id)
                        self.write_user_message(current_event)

                    if current_event.is_mention:
                        self.write_user_mentions(current_event.user_id, current_event.mentioned_users)

                    self.events.pop(0)
                sleep(1)

    def write_user_shell(self, user_id, real_name, display_name):
        new_doc = {
            'updated': datetime.utcnow(),
            'user_id': user_id,
            'real_name': real_name,
            'display_name': display_name,
            'posts': 0,
            'words': 0,
            'avg_words': 0,
            'images': 0,
            'snippets': 0,
            'files': 0,
            'total_data': 0,
            'bot_calls': 0,
            'bot_thanks': 0,
            'mentions': 0,
            'mentioned': 0,
            'emojis_used': 0,
            'reactions_to': 0,
            'reactions_from': 0
        }
        self.mongo.insert_document(new_doc)

    def write_user_reactions(self, to_user, from_user):
        # user reacted TO something
        query = {"user_id": to_user}
        current = self.mongo.find_document(query)
        update = {
            "$set": {
                'updated': datetime.utcnow(),
                'reactions_to': current['reactions_to'] + 1
            }
        }
        self.mongo.update_document(query, update)

        # user RECEIVED reaction
        query = {"user_id": from_user}
        current = self.mongo.find_document(query)
        update = {
            "$set": {
                'updated': datetime.utcnow(),
                'reactions_from': current['reactions_from'] + 1
            }
        }
        self.mongo.update_document(query, update)

    def write_user_mentions(self, to_user, from_users):
        # user that did the mentioning
        query = {"user_id": to_user}
        current = self.mongo.find_document(query)
        update = {
            "$set": {
                'updated': datetime.utcnow(),
                'mentions': current['mentions'] + 1
            }
        }
        self.mongo.update_document(query, update)

        # user(s) that were mentioned:
        for u in from_users:
            query = {"user_id": u}
            current = self.mongo.find_document(query)
            update = {
                "$set": {
                    'updated': datetime.utcnow(),
                    'mentioned': current['mentioned'] + 1
                }
            }
            self.mongo.update_document(query, update)

    def write_user_message(self, event):
        # write the bulk of the stuff here
        query = {"user_id": event.user_id}
        current = self.mongo.find_document(query)
        update = {
            "$set": {
                'updated': datetime.utcnow(),
                'posts': current['posts'] + 1,
                'words': current['words'] + event.words,
                'avg_words': (current['words'] + event.words) / (current['posts'] + 1),
                'images': current['images'] + event.images,
                'snippets': current['snippets'] + event.snippets,
                'files': current['files'] + event.files,
                'total_data': current['total_data'] + event.data,
                'bot_calls': current['bot_calls'] + event.bot_calls,
                'bot_thanks' : current['bot_thanks'] + event.bot_thanks,
                'emojis_used': current['emojis_used'] + event.emojis_used
            }
        }
        self.mongo.update_document(query, update)

    def add_event(self, event):
        if event["type"] in self.allowed_events and "subtype" not in event:
            self.events.append(event)
