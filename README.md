# Noob SNHUbot

A simple Slack bot written in Python for the [snhu_coders](https://snhu_coders.slack.com) Slack workgroup. It's a simple and fun side project for me, and anyone else is welcome to participate. Contact me on Slack or open an issue if you'd like to see an enhancement to the bot.

## Current State

Noob SNHUbot loads a series of commands and can execute them when prompted by a user through the Slack channel.  It only utilizes the Slack Client [RTM API](https://api.slack.com/rtm). The [Events](https://api.slack.com/events) and [Web](https://api.slack.com/web) APIs have not been utilized, but may be implemented at a later time.

## Functionality

Noob SNHUbot will respond to the following direct messages. To begin a conversation, start a message in the channel with `@Noob SNHUbot`:

* catalog
  * Uses SNHU Course Catalog Data to fetch details about course subjects and course IDs.
  * catalog `subject` returns a list of Course IDs for the given subject:
    * `catalog Computer Science`
  * catalog `courseID` will return an attachment with catalog data for the course:
    * `catalog CS499`
  * catalog `courseID1 courseID2 courseID3` will return attachments for up to three course IDs.
  * Acceptable formats for course ID are: `ABC-123`, `ABC 123`, or `ABC123`, case insensitive.
* channels
  * Displays a detailed list of channels in the Slack workgroup.
* help
  * Shows a list of known commands.
* it140
  * Gives links to tutorial videos pertaining to course material in IT-140.
  * Requires secondary command to indicate desired topic: `@Noob SNHUbot it140 topic`.
  * Valid secondary commands are:
    * `help`: gives a list of valid commands.
    * `basics`: gives video links pertaining to Python basics.
    * `dicts`: gives video links pertaining to Python dictionaries.
    * `files`: gives video links pertaining to Python file handling.
    * `functions`: gives video links pertaining to Python functions.
    * `lists`: gives video links pertaining to Python lists.
    * `project`: gives video links pertaining to the various script projects in IT-140.
    * `regex`: gives video links pertaining to regular expressions in Python. 
* leaderboard:
    * Work in progress.  Aiming to allow users access to various post metrics.
* packtbook
  * Reaches out to the Packtbook Website to display the latest free book of the day.
  * `packtbook mini` will show the attachment in a smaller format.
  * Automatically scheduled to launch at 8:30PM Eastern Time.
* roll `XdY[±Z]`
  * Rolls X number of Y-Sided dice with a + or - Z modifier!
  * Invalid rolls will respond with _"That roll is not valid. Try `@Noob SNHUbot roll help`"_
  * `roll help` will respond with a help message that explains the syntax with examples
  * Valid rolls respond with a Slack [Attachment](https://api.slack.com/docs/message-attachments) message indicated the total value of the roll, what roll is operated on, individual roll values, and the modifier applied
* what is the airspeed velocity of an unladen swallow?
  * A clever joke.
  * Responds with a Youtube video to a Monty Python and the Holy Grail clip.
* what's my name?
  * Simple call and response.
  * Resonds with: _"Your name is `<@{name}>`! Did you forget or something?"_

### Modular Commands

Commands are now modular! Command scripts are stored in the `cmds` module.  When loaded, the module
will dynamically load all commands and store them in a series of lists depending on their public flag.
In order to use them, the command script must follow these strict guidelines:

* `command` variable
  * The `command` variable must be defined. It is used to identify the command trigger for the bot.
* `public` variable
  * Boolean value if the command should be publicly callable by users or privately used internally by the bot itself.
* `execute(command, user)`
  * The `execute()` function must be defined and accept `command` and `user` variables from the bot.
  * The `execute()` function must return `response` and `attachment`. These can be set to `None`.

#### Command Module Example

```python
command = "test"
public = True

def execute(command, user):
    attachment = None
    response = "This is just an example."

    return response, attachment
```

### Configuration

The preferred method to configure the bot is now YAML. A `config.yml` in the root folder of the project
should contain the client token and Mongo DB (optional) configurations.

Sample `config.yml`:

```yaml
slackbot:
  token: xoxb-123456789012-aBcDeFgHiJkLmNoPqRsTuVwXyZ  
mongo:  
  db: my_database
  collections:
    conn: conn_log
    cmds: cmd_log
    leaderboard: lb_log
  hostname: my_db_server
  port: 27017
```

Mongo DB logging is optional and can be omitted from the configuration file. If the config is present, `leaderboard` can
be omitted specifically to disable event tracking.

Additionally, the `config.yml` file can be omitted to fall back on utilizing the `SLACK_CLIENT` environment variable.

### Scheduled Tasks

COMING SOON!

## Contributing

If you'd like to contribute, join us on the Slack workspace mentioned above. All SNHU students are welcome.
