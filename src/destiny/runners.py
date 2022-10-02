# Entry point for the bot, this file exists mostly to implement restarts


import importlib
import destiny.homeworkbot
import destiny.message_handler

def auto_reload(client):
    while True:
        client.run()
        importlib.reload( homeworkbot )
    
