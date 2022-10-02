import importlib
import homeworkbot
import message_handler

while True:
    homeworkbot.Client(message_handler.message_handler).run()
    importlib.reload( homeworkbot )
    
