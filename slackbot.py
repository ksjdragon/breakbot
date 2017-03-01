import time
import datetime
import pickle
from slackclient import SlackClient
from random import randint
import sys

BOT_ID = sys.argv[1]
dt = datetime.datetime
f = open('date.dat','rb')
targetDate = pickle.load(f)
f.close()

# constants
AT_BOT = "<@" + BOT_ID + ">"
EXAMPLE_COMMAND = "do"

# instantiate Slack & Twilio clients
slack_client = SlackClient(sys.argv[2])

def handle_command(command, channel):
    global targetDate
    global dt
    response = "Not sure what you mean. Try @break help!"
    if command.startswith("days left in hell"):
        response = "You have *" + str((targetDate.date() - dt.now().date()).days) + "* days left."

    elif command.startswith("time left in hell"):
        timeDelta = str(targetDate - dt.now()).replace(":0",":")
        if "," not in timeDelta:
            other = " "+timeDelta
            days = "0 days"
        else:
            days, other = timeDelta.split(",")
        hours, minutes, seconds = other.split(":")
        response = "Only " + days + ","+hours+" hours, "+minutes+" minutes, and "+seconds.split(".")[0]+" seconds left!"

    elif command.startswith("summary"):
        timeDelta = str(targetDate - dt.now()).replace(":0",":")
        if "," not in timeDelta:
            other = " "+timeDelta
            days = "0 days"
        else:
            days, other = timeDelta.split(",")
        hours, minutes, seconds = other.split(":")
        approx = [
            str((targetDate.date() - dt.now().date()).days) + " days, ",
            str(int(hours) + int(days.replace(" days",""))*24) + " hours, ",
        ]
        approx.append(str(int(minutes)+int(approx[1].replace(" hours, ",""))*60)+" minutes, or ")
        approx.append(str(int(minutes)+int(approx[2].replace(" minutes, or ",""))*60)+" seconds.")
        
        first = "The current target date is *" + targetDate.strftime("%B %d, %Y") + "*!"
        second = "There are " + days + ","+hours.lstrip("0")+" hours, "+minutes.lstrip("0")+" minutes, and "+seconds.split(".")[0].lstrip("0")+" seconds left!"
        third = "Other representations are: " + "".join(approx);
        response = first+"\n"+second+"\n"+third

    elif command.startswith("set new time "): 
        newDate = command.replace("set new time ","").split(" ")
        time = list(map(int, newDate[3].split(":")))
        if newDate[4] == "pm":
            if time[0] != 12:
                 time[0] += 12
        elif newDate[4] == "am" and time[0] == 12:
            time[0] -= 12
        try:
            newDate = dt(int(newDate[2]),int(newDate[0]),int(newDate[1]),time[0],time[1])
            if(newDate < dt.now()):
                response = "Please enter in a date after today!"
            else:
                targetDate = newDate
                print(targetDate)
                f = open('date.dat', 'wb')
                pickle.dump(targetDate,f)
                f.close()
                response = "Ok! Your new date is *" + targetDate.strftime("%B %d, %Y %I:%M %p").replace(" 0"," ") + "*!"
        except ValueError:
            response = "That's an invalid date! The format is: *Day Month Year Hour:Minute AM/PM*"

    elif command.startswith("target date"):
        response = "The current target date is *" + targetDate.strftime("%B %d, %Y %I:%M %p").replace(" 0"," ") + "*!"
    elif command.startswith("flip a coin"):
        coin = ["Heads!", "Tails!"]
        response = coin[randint(0,1)]    
    elif command.startswith("?") or command.lower().startswith("help"):
        commands = [
            "Summary: Gives a summary of all information.",
            "Days left in hell: Gives days left to date.",
            "Time left in hell: Gives countdown left to date.",
            "Set new time [Day Month Year Hour:Minute AM/PM]: Sets new target date.",
            "Target date: Gives current target date.",
            "Flip a coin: Gives heads or tails."
        ]
        response = "My current commands are:```"+'\n'.join(commands)+"```"
    slack_client.api_call("chat.postMessage", channel=channel,text=response, as_user=True)
def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']

    return None, None

if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("Bot connected and running!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
