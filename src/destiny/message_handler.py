from destiny.header import *
from destiny.exceptions import HardReset, SoftReset
import asyncio
import requests
import os
import json
from destiny.convenience import api_post, draft


# DEST_DIR = "../assets/hw"

def restart():
    import sys
    print(f"argv was",sys.argv)
    print(f"sys.executable was", sys.executable)
    print(f"restart now")

    import os
    os.execv(sys.executable, ['python'] + sys.argv)

async def message_handler( js, shared_info, voice_info, session_id=None, user=None ):
    message = js["d"]
    if not message["author"]["id"] == user["id"]:
        if message["content"] == f"ping": 
            print( f"I am { user['id'] } f" )
            channel_id = message["channel_id"]
            reply_json = dict()
            reply_json["message_reference"] = { f"message_id" : message["id"], f"channel_id" : message["channel_id"], f"guild_id" : message["guild_id"] }
            reply_json["content"] = f"Pong indeed, <@{message['author']['id']}>!"
            reply_json["components"] = []
            api_post( f"channels/{channel_id}/messages", reply_json )



        elif len(message["content"].split())  > 1:
            mlist = message["content"].split()
            if mlist[0] == f"hw" or mlist[0] == f"Hw" or mlist[0] == f"HW":

                subjects = os.listdir( f"{ DEST_DIR }" )
                for i in subjects:
                    if mlist[1] in os.listdir( f"{ DEST_DIR }/{i}" ):
                        mlist.insert( 1, i )
                        mlist.insert( 1, f"pull" )
                    elif len(mlist) > 2:
                        if mlist[2] in os.listdir( f"{ DEST_DIR }/{i}" ):
                            mlist.insert( 2, i )
                    

                if mlist[1] in subjects:
                    print( f"[blue]Found {mlist[1]} in subjects!" )
                    mlist.insert( 1, f"pull" )
                        
                
                send_reply = True

                channel_id = message["channel_id"]

                reply_json = dict()
                reply_json["components"] = None
                try:
                    verb = mlist[1]
                    subject = mlist[2]
                    if subject not in os.listdir( f"{ DEST_DIR }" ):
                        print( f"{ subject } not in { subjects }" )
                        for i in subjects:
                            print( f"Checking {i}" )
                            assignments = os.listdir( f"{ DEST_DIR }/{ i }" )
                            print( assignments )
                            try:
                                if subject in assignments:
                                    print( f"Found { subject } in { i }" )
                                    assignment = subject
                                    subject = i
                                    person = mlist[3]
                                    print( f"Could assign person" )
                                    rating = mlist[1]
                                    print( f"Could assign rating" )
                                    break
                                else:
                                    print( f"{subject} not in { assignments }" )
                            except Exception as e:
                                print( f"[red]Should not be here cuz {e}" )
                                print( f"Not enough args for rate, pull or push" )
                                print( subject, assignment )
                    else:
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
                            with open( f"{ DEST_DIR }/{ subject }/{ assignment }/{message['author']['username']}.pdf", f"wb") as f:
                                f.write( r.content )
                            ratings = json.load( open( f"{ DEST_DIR }/{ subject }/{ assignment }/.ratings.json" ) )
                            ratings[ message[ f"author" ][ f"username"] ] = { f"ratings" : [] }
                            reply_json["content"] = f"Recieved! Thank you!"
                        except IndexError as e:
                            reply_json["content"] = f"Not enough arguments (probably) f"

                    case "pull" | "get" :
                        if f"person" not in locals():
                            ratings = json.load( open( f"{ DEST_DIR }/{ subject }/{ assignment }/.ratings.json" ) )
                            
                            max_rating = { f"rate_value" : 0 }
                            print( ratings )
                            for i in ratings.keys():
                                if i == f"Name":
                                    continue
                                if ratings[i]["rate_value"] > max_rating["rate_value"] :
                                    max_rating = ratings[i]
                                    person = i
                            api_post( f"channels/{channel_id}/messages", None, files= { f"{ DEST_DIR }.pdf" : open( f"{ DEST_DIR }/{ subject }/{ assignment }/{ person }.pdf", f"rb" )}  )
                            send_reply = False
                            
                        elif os.path.exists( f"{ DEST_DIR }/{ subject }/{ assignment }/{ person }.pdf" ):
                            reply_json["content"] = f"Here you go"
                            api_post( f"channels/{channel_id}/messages", None, files= { f"{ DEST_DIR }.pdf" : open( f"{ DEST_DIR }/{ subject }/{ assignment }/{ person }.pdf", f"rb" )}  )
                            send_reply = False
                        else:
                            reply_json["content"] = f"Syntax incorrect"

                    case "list" | "ls" : 
                        try:
                            if  f"subject" not in locals(): #List subjects
                                reply_json["content"] = f", f".join( subjects ) 
                            elif  f"assignment" not in locals(): #List assignments
                                reply_json["content"] = f", f".join( os.listdir( f"{ DEST_DIR }/{ subject }" ) )
                            elif f"person" not in locals(): #List files
                                msg_draft = f""
                                
                                ratings = json.load( open( f"{ DEST_DIR }/{ subject }/{ assignment }/.ratings.json" ) )
                                for i in ratings.keys():
                                    try:
                                        msg_draft += f"{ i }:\t { ratings[ i ][ 'rate_value' ] }\n"
                                    except:
                                        msg_draft += f"Assignment: { ratings[ i ] }\n\n"
                                reply_json["content"] = msg_draft

                        except IndexError as e:
                            reply_json["content"] = f"Not enough arguments (probably) f"
                        except Exception as e:
                            reply_json["content"] = f"Failed" + str( e )
                        
                                
                    case "create":
                        try:
                            try:
                                os.mkdir( f"{ DEST_DIR }/{mlist[2]}/{mlist[3]}" )
                            except:
                                reply_json["content"] = f"Already exists!"
                            ratings = dict()
                            ratings["Name"] = mlist[3]
                            with open( f"{ DEST_DIR }/{mlist[2]}/{mlist[3]}/.ratings.json", f"w"  ) as f:
                                f.write( json.dumps( ratings ) )
                            reply_json["content"] = f"Success"
                        except IndexError as e:
                            reply_json["content"] = f"Not enough arguments (probably) f"
                        except Exception as e:
                            reply_json["content"] = f"Failed" + str( e )
                            
                    case "rate":
                        if len(mlist) ==  6:
                            if rating > 0 and rating < 6: 

                                ratings = json.load( open( f"{ DEST_DIR }/{subject}/{assignment}/.ratings.json") )

                                if person in ratings.keys():
                                    ratings[ person ][ f"ratings" ].append( rating )
                                    ratings[ person ]["rate_value" ]  = sum( ratings[ person ][ f"ratings" ] ) / len( ratings[ person ][ f"ratings" ] )
                                else:
                                    ratings[ person ] = dict()
                                    ratings[ person ][ f"ratings" ] = [ rating ]
                                    ratings[ person ][ f"rate_value" ] = rating
                                    

                                with open( f"{ DEST_DIR }/{subject}/{assignment}/.ratings.json", f"w"  ) as f:
                                    f.write( json.dumps( ratings ) )
                                reply_json["content"] = f"Thanks for rating!"
                            else: 
                                reply_json["content"] = f"Rate between 1 and 5 please"
                        else:
                            reply_json["content"] = f"Syntax is \"hw rate _subject_ _assignment_ _user_ _rating_\""
                            
                    case "join":
                        resp = json.loads( api_post( f"guilds/{ message['guild_id'] }/channels", None, method="GET" ).content.decode() )
                        voice_channels = [ i for i in resp if i["type"] == 2 ]
                        print( voice_channels )

                        for i in voice_channels:
                            pass

                        # This is pretty much arbritratry, wil change later
                        voice_channel = voice_channels[1]

                        reply_json["content"] = f"Joining {voice_channel['name']}!"

                        await shared_info.put( draft( VOICE_CONNECT, guild=message["guild_id"], channel=voice_channel["id"] ) )
                        
                    
                    case "leave":
                        reply_json["content"] = f"Leaving..."
                        await shared_info.put( draft( VOICE_CONNECT, guild=message["guild_id"] ) )

                    case "restart":

                        reply_json["content"] = f"Soft Reset"
                        api_post( f"channels/{channel_id}/messages", reply_json ).content 
                        raise SoftReset

                    case "restart_hard":
                        print( f"[red]!!!" )
                        allowed_role = f"919190731065806878" 
                        if allowed_role in js["d"]["member"]["roles"]:
                            reply_json["content"] = f"Hard Reset!"
                            api_post( f"channels/{channel_id}/messages", reply_json ).content 
                            raise HardReset
                        else:
                            reply_json["content"] = f"Only <@{allowed_role}> can hard reset"
                    case _:
                        reply_json["content"] = f"{mlist[1]} does not look like a subject, assignment or verb"
                    
                            

                
                if send_reply:
                    print( reply_json )
                    print( api_post( f"channels/{channel_id}/messages", reply_json ).content )
                else:
                    send_reply = True
