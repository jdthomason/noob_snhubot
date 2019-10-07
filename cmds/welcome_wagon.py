
command = "welcome wagon"
public = True


def execute(command, user, bot):
    attachment = None

    split_command = command.split(" ")

    if len(split_command) > 2:
        if split_command[2] == "join":
            response = "You have elected to join the welcome wagon."
        elif split_command[2] == "leave":
            response = "You have elected to leave the welcome wagon."
        elif split_command[2] == "inactive":
            response = "You wish to take a break from the welcome wagon"
        elif split_command[2] == "active":
            response = "You wish to set yourself as active again."
        else:
            response = "I'm not sure what you want to do.  Your options are: `join`, `leave`, `inactive`, or `active`."
    else:
        response = "Here are the options for the welcome wagon:\n\n" \
            "`@Noob_SNHUbot welcome wagon join`: enters you into the welcome wagon.\n" \
            "`@Noob_SNHUbot welcome wagon leave`: takes you out of the welcome wagon.\n" \
            "`@Noob_SNHUbot welcome wagon inactive`: gives you a break from the welcome wagon.\n" \
            "`@Noob_SNHUbot welcome wagon active`: puts you back into the welcome wagon."

    return response, attachment