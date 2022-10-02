from convenience import *
import requests
import os
import json
from rich import pretty
from rich import print
pretty.install()

async def message_handler( js, shared_info, voice_info, session_id=None, user=None ):
    message = js["d"]
    if not message["author"]["id"] == user["id"]:
        if message["content"] == "ping": 
            print( f"I am { user['id'] } " )
            channel_id = message["channel_id"]
            reply_json = dict()
            reply_json["message_reference"] = { "message_id" : message["id"], "channel_id" : message["channel_id"], "guild_id" : message["guild_id"] }
            reply_json["content"] = f"Pong indeed, <@{message['author']['id']}>!"
            reply_json["components"] = []
            api_post( f"channels/{channel_id}/messages", reply_json )

async def cg_handler( js, shared_info, voice_info, session_id=None, user=None ):
    pass
async def misc_handler( js, shared_info, voice_info, session_id=None, user=None ):
    print( js )
