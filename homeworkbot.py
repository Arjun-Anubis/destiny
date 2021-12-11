#!/bin/python3

from pprint import pprint
import uuid
import random
import os.path
import os
import requests
import sys
import asyncio
import websockets
import json


IDENTIFY=2
VOICE_CONNECT=4

voice_url = None
rest_url = "https://discordapp.com/api/"
#rest_url = "http://localhost:4001/"
with open( "token" ) as f:
    token = f.read()[:-1] #Removing newline

headers = { "Authorization" : f"Bot {token}", "User-Agent" : "DiscordBot (https://github.com/Arjun-Anubis/snowflake, v0.1)" }

presence = dict()
presence["since"] = 91879201
presence["activities"] = [{"name" : "Serving ya homewerk!, source code at https://github.com/Arjun-Anubis/snowflake", "type" : 0 }]
presence["status"] = "online"
presence["afk"] = False

user = dict()
session_id = ""
voice_guild_id = None
heartbeat_interval = 0
seq_no = 0
buffer_send = None
buffer_response = None
voice_token = None
def api_post( subdivision, data, files=None, method="POST" ):
    try:
        if not files:
            if data:
                response = requests.request( method,  f"{rest_url}{subdivision}", json=data, headers=headers )
                print(response)

            else:
                response = requests.request( method,  f"{rest_url}{subdivision}", headers=headers )
                print(response)

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

 
async def send( websocket ):
    global buffer_response
    global buffer_send
    while True:
        if buffer_send:
            print( f"Sending { buffer_send }" )
            resp = await websocket.send( buffer_send )
            pprint(resp)
            buffer_response = resp
            buffer_send = None
        else:
            await asyncio.sleep(0.5)
        
async def recieve(websocket):
    global voice_token
    global voice_url
    global user
    global heartbeat_interval
    global seq_no
    global session_id
    global voice_guild_id


    await websocket.send( draft( IDENTIFY ) )
    while True:
        inc =  await websocket.recv()
        js = json.loads(inc)
        if js["s"]:
            seq_no = int(js["s"])

        match js["op"]:
            case 0:
                pprint(js)
                match js["t"]:
                    case "READY":
                        print( "Recieved READY" )
                        user = js["d"]["user"]
                        session_id = js["d"]["session_id"]
                        print( session_id )
                    case "MESSAGE_CREATE":
                        print( "!! Message create" )
                        message_handler( js ) 
                    case "VOICE_SERVER_UPDATE":
                        print( "Handling voice now" )
                        voice_url = f'wss://{ js[ "d" ][ "endpoint" ] }'
                        voice_guild_id = js[ "d" ][ "guild_id" ]
                        voice_token = js[ "d" ][ "token" ]
                    case _:
                        print( f"Type: {js['t']}" )
            case 10:
                heartbeat_interval = int(js["d"]["heartbeat_interval"])
                
            case 11:
                pass
            case _:
                pprint(js)
        
    

async def heart_beat( websocket ):
    await asyncio.sleep(0.5)
    await websocket.send( json.dumps( { "op" : 1, "d" : seq_no+1  } ).encode() )
    while True:
        await asyncio.sleep( heartbeat_interval/1000 ) #milisecond to second
        await websocket.send( json.dumps( { "op" : 1, "d" : seq_no+1  } ).encode() )

async def voice_beat( voice_socket, voicebeat_interval ):
    print( "Voice beat" )
    resp =  json.dumps( { "op" : 3, "d" : 1501184119561 } )
    pprint(resp)
    await voice_socket.send( resp )
    
    while True:
        await asyncio.sleep( voicebeat_interval/1000 ) #milisecond to second
        resp =  json.dumps( { "op" : 3, "d" : uuid.uuid4().int } )
        print( resp )
        await voice_socket.send( resp )
    
async def voice_handle( voice_socket ):
    print( "Voice handle" )
    while True:
        print( "Waiting" )
        js = json.loads( await voice_socket.recv() )
        pprint( js )
        match js[ "op" ]: 
            case _:
                print( "Voice recieve" )
    
async def voice( ):
    global voice_url
    while not voice_url:
        await asyncio.sleep(0.5)

    async with websockets.connect( voice_url ) as voice_socket:

        print( "Works" ) 
        js = json.loads( await voice_socket.recv() )
        if js[ "op" ] == 8:
            print( js )
            print( "OP8" )
            print( "Sending auth" )
            resp = json.dumps( { "op" : 0, "d" : { "server_id" : voice_guild_id, "user_id" : user["id"], "session_id" : session_id, "token" : voice_token } } )
            print(resp)
            await voice_socket.send( resp )
            op2 = await voice_socket.recv()
            op2 = json.loads( op2 )
            print( f"ip: { op2['d']['ip'] }" ) 
            print( f"port: { op2['d']['port'] }" ) 
            voice_handle_task = asyncio.create_task( voice_handle( voice_socket ) )
            voice_beat_task = asyncio.create_task( voice_beat( voice_socket , js[ "d" ][ "heartbeat_interval" ] ) )
            await voice_beat_task
            await voice_handle_task
                    
                    
async def main(url):
    async with websockets.connect(url) as websocket:
        recv_task = asyncio.create_task( recieve( websocket ) )
        heartbeat_task  = asyncio.create_task( heart_beat( websocket ) )
        send_task = asyncio.create_task( send( websocket ) )
        voice_task = asyncio.create_task( voice() )
        await recv_task
        await heartbeat_task
        await send_task
        await voice_task
        print( "All done!" )
        
def message_handler( js ):
    global buffer_response
    global buffer_send
    message = js["d"]
    if not message["author"]["id"] == user["id"]:
        if message["content"] == "ping": 
            channel_id = message["channel_id"]
            reply_json = dict()
            reply_json["message_reference"] = { "message_id" : message["id"], "channel_id" : message["channel_id"], "guild_id" : message["guild_id"] }
            reply_json["content"] = f"Pong indeed, <@{message['author']['id']}>!"
            reply_json["components"] = []
            api_post( f"channels/{channel_id}/messages", reply_json )



        elif len(message["content"].split())  > 1:
            if message["content"].split()[0] == "hw":

                send_reply = True
                mlist = message["content"].split()

                channel_id = message["channel_id"]

                reply_json = dict()
                reply_json["components"] = None
                try:
                    verb = mlist[1]
                    subject = mlist[2]
                    assignment = mlist[3]
                    person = mlist[4]
                    rating = int( mlist[5] )
                except:
                    pass

                match mlist[1]:

                    case "push" | "add" :
                        try: 
                            print(message["attachments"][0]["url"])
                            r = requests.get( message["attachments"][0]["url"] )
                            with open( f"hw/{mlist[2]}/{mlist[3]}/{message['author']['username']}.pdf", "wb") as f:
                                f.write( r.content )
                            ratings = json.load( open( f"hw/{ subject }/{ assignment }/.ratings.json" ) )
                            ratings[ message[ "author" ][ "username"] ] = { "ratings" : [] }
                            reply_json["content"] = "Recieved! Thank you!"
                        except IndexError as e:
                            reply_json["content"] = "Not enough arguments (probably) "

                    case "pull" | "get" :
                        try:
                            if os.path.exists( f"hw/{mlist[2]}/{mlist[3]}/{mlist[4]}.pdf" ):
                                reply_json["content"] = "Here you go"
                                reply_json["attachments"] = [ { "id" : 0, "filename" : "hw.pdf" } ]
                                api_post( f"channels/{channel_id}/messages", None, files= { "hw.pdf" : open( f"hw/{mlist[2]}/{mlist[3]}/{mlist[4]}.pdf", "rb" )}  )
                                send_reply = False
                            else:
                                reply_json["content"] = "Syntax incorrect"
                        except IndexError as e:
                            reply_json["content"] = "Not enough arguments (probably) "
                        except Exception as e:
                                reply_json["content"] = "Failed" + str(e)

                    case "list" | "ls" : 
                        try:
                            if len(mlist) == 2: #List subjects
                                reply_json["content"] = ", ".join( os.listdir( "hw" ) ) 
                            elif len(mlist) == 3: #List assignmentsj
                                for i in os.listdir("hw"):
                                    if mlist[2] == i:
                                        reply_json["content"] = ", ".join( os.listdir( f"hw/{ i }" ) )
                            elif len(mlist) == 4: #List files
                                msg_draft = ""
                                
                                ratings = json.load( open( f"hw/{ subject }/{ assignment }/.ratings.json" ) )
                                for i in ratings.keys():
                                    try:
                                        msg_draft += f"{ i }:\t { ratings[ i ][ 'rate_value' ] }\n"
                                    except:
                                        msg_draft += f"Assignment: { ratings[ i ] }\n\n"
                                #reply_json["content"] = ",".join( os.listdir( f"hw/{ mlist[2] }/{ mlist[3] }/" ) )
                                reply_json["content"] = msg_draft

                        except IndexError as e:
                            reply_json["content"] = "Not enough arguments (probably) "
                        except Exception as e:
                            reply_json["content"] = "Failed" + str( e )
                        
                                
                    case "create":
                        try:
                            try:
                                os.mkdir( f"hw/{mlist[2]}/{mlist[3]}" )
                            except:
                                reply_json["content"] = "Already exists!"
                            ratings = dict()
                            ratings["Name"] = mlist[3]
                            with open( f"hw/{mlist[2]}/{mlist[3]}/.ratings.json", "w"  ) as f:
                                f.write( json.dumps( ratings ) )
                            reply_json["content"] = "Success"
                        except IndexError as e:
                            reply_json["content"] = "Not enough arguments (probably) "
                        except Exception as e:
                            reply_json["content"] = "Failed" + str( e )
                            
                    case "rate":
                        if len(mlist) ==  6:
                            if rating > 0 and rating < 6: 

                                ratings = json.load( open( f"hw/{subject}/{assignment}/.ratings.json") )

                                if person in ratings.keys():
                                    ratings[ person ][ "ratings" ].append( rating )
                                    ratings[ person ]["rate_value" ]  = sum( ratings[ person ][ "ratings" ] ) / len( ratings[ person ][ "ratings" ] )
                                else:
                                    ratings[ person ] = dict()
                                    ratings[ person ][ "ratings" ] = [ rating ]
                                    ratings[ person ][ "rate_value" ] = rating
                                    

                                with open( f"hw/{subject}/{assignment}/.ratings.json", "w"  ) as f:
                                    f.write( json.dumps( ratings ) )
                                reply_json["content"] = "Thanks for rating!"
                            else: 
                                reply_json["content"] = "Rate between 1 and 5 please"
                        else:
                            reply_json["content"] = "Syntax is \"hw rate _subject_ _assignment_ _user_ _rating_\""
                            
                    case "join":
                        resp = json.loads( api_post( f"guilds/{ message['guild_id'] }/channels", None, method="GET" ).content.decode() )
                        channel_id = ""
                        for i in resp:
                            if i["type"] == 2:
                                reply_json["content"] = f"Found voice channel { i[ 'name' ] } "
                                channel_id = i[ "id" ]
                        buffer_send = ( draft( VOICE_CONNECT, guild=message["guild_id"], channel=channel_id ) )
                    
                    case "leave":
                        buffer_send = draft( VOICE_CONNECT, guild=message["guild_id"] )
                    case _:
                        reply_json["content"] = f"Invalid verb, use hw pull to get hw, pulling without verb will be added soon"
                            

                
                if send_reply:
                    api_post( f"channels/{channel_id}/messages", reply_json )
                else:
                    send_reply = True

asyncio.run(main("wss://gateway.discord.gg"))
