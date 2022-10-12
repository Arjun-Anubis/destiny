# Entry point for the bot, this file exists mostly to implement restarts
# import destiny.message_handler

def auto_reload(client):
    while True:
        client.run()
    
