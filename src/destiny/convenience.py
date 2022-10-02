from destiny.header import *
import os
import requests
import json

presence = dict()
presence["since"] = 91879201
presence["activities"] = [{"name" : "Serving ya homewerk!, source code at https://github.com/Arjun-Anubis/snowflake", "type" : 0 }]
presence["status"] = "online"
presence["afk"] = False

rest_url = "https://discordapp.com/api/"
headers = { "Authorization" : f"Bot {token}", "User-Agent" : "DiscordBot (https://github.com/Arjun-Anubis/snowflake, v0.1)" }

def api_post( subdivision, data, files=None, method="POST" ):
    try:
        if not files:
            if data:
                response = requests.request( method,  f"{rest_url}{subdivision}", json=data, headers=headers )
                print(response)
            else:
                response = requests.request( method,  f"{rest_url}{subdivision}", headers=headers )

        else:
            response = requests.post( f"{rest_url}{subdivision}",  headers=headers, files=files )
            
        return response
            
    except Exception as e:
        print(e)
def draft( code ,guild=None, channel=None ):

    response = {  "op" : code }
    d = {}
    
    match code:
        case 2:
            d["token"] = token
            d["intents"] = 641
            d["properties"] = { "$os" : "linux", "$browser" : "anubi", "$device": "anubi" }
            d["presence"] = presence
        case 4:
            d["guild_id"] = guild
            d["channel_id"] = channel
    response["d"] = d
    return json.dumps( response )
