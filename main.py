import config
import telebot
import s_taper
from s_taper.consts import *

reminderDB = s_taper.Taper("reminders", "reminders.db").create_table({"reminderId": INT+KEY, "localId": INT, "userId":INT, "title": TEXT, "contents":TEXT})


bot = telebot.TeleBot(config.key)

def strgspn(msg, target, isStrspn):
    index = 0
    if msg[index] in ['\'', '"', '`']:
        quoteState = msg[index]
        index += 1
    else:
        quoteState = None
    while index < len(msg) and (isStrspn == (msg[quoteState == None if index else index + 1] in target)) and (quoteState == None or quoteState == msg[index+1]):
        index += 1
    return [index, quoteState != None]

def strspn(msg, target):
    return strgspn(msg, target, True)

def strnspn(msg, target):
    return strgspn(msg, target, False)

WHITESPACE = " \t\n"


argMap = [
  {"short":"h", "long":"help", "haveArg":False, "restrict":"global"},
  {"short":"t", "long":"title", "haveArg":True, "restrict":"add"}
]

def h1(arg, args, typekey):
    for i, a in enumerate(args):
        if a[typekey] == arg:
            return i
    return None

class NoValue:
    pass

def phrase(msg, args, mode):
    outputs = {"resultType": "ast", "v":[], "kv":{}}
    index = 0
    lastKey = None
    while True:
        index += strspn(msg[index:], WHITESPACE)
        if index >= len(msg):
            break
        if msg[index] == '-':
            index += 1
            if msg[index] == '-':
                index += 1
                arg = msg[index:index+strnspn(msg[index:], WHITESPACE)]
                index += strnspn(msg[index:], WHITESPACE)
                lastKey = h1(arg, args, "long")
                if lastKey == None or not args[lastKey]["restrict"] in ["global", mode]:
                    return {"resultType": "error", "description":f'Unkown argument "{arg}"'}
                   
            else:
                while index < len(msg) and msg[index] not in WHITESPACE:
                    arg = msg[index]
                    lastKey = h1(arg, args, "short")
                    if lastKey == None:
                        return {"resultType": "error", "description":f'Unkown argument "{arg}"'}
                    index += 1
            outputs["kv"][lastKey] = NoValue
        else:
            newIndex = index + strnspn(msg[index:], WHITESPACE)
            if lastKey != None and outputs["kv"][lastKey] == NoValue and args[lastKey]["haveArg"]:
                outputs["kv"][lastKey] = msg[index:newIndex]
            else:
                outputs["v"].append(msg[index:newIndex])
            index = newIndex
    return outputs

@bot.message_handler(func= lambda m: m.text.startswith("/add"))
def add_handle(m):
    ast = phrase(m.text)
    print(ast)
    reminderDB.write([len(reminderDB.read_all()), len(reminderDB.read("userId", m.from_user.id)), m.from_user.id, "Untitled", m.text[4:]])
    bot.send_message(m.chat.id, "Added note")

@bot.message_handler(func= lambda m: m.text.startswith("/del"))
def del_handler(m):
    for row in reminderDB.read_all():
        if (row[2] == m.from_user.id and row[1] == None ):
            pass
    reminderDB.delete_row("reminderId", )

@bot.message_handler(func= lambda m: m.text.startswith("/ls"))
def ls_handle(m):
    all = reminderDB.read("userId", m.from_user.id)
    msg = ""
    for reminder in all:
        msg += f"{reminder[1]}. {reminder[4]}\n"
    bot.send_message(m.chat.id, msg)

bot.infinity_polling()
