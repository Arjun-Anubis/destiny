from header import *
import os
import json
from convenience import api_post, draft


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



        elif len(message["content"].split())  > 1:
            mlist = message["content"].split()
            if mlist[0] == "hw" or mlist[0] == "Hw" or mlist[0] == "HW":

                subjects = os.listdir( "hw" )
                for i in subjects:
                    if mlist[1] in os.listdir( f"hw/{i}" ):
                        mlist.insert( 1, i )
                        mlist.insert( 1, "pull" )
                    elif len(mlist) > 2:
                        if mlist[2] in os.listdir( f"hw/{i}" ):
                            mlist.insert( 2, i )
                    

                if mlist[1] in subjects:
                    print( f"[blue]Found {mlist[1]} in subjects!" )
                    mlist.insert( 1, "pull" )
                        
                
                send_reply = True

                channel_id = message["channel_id"]

                reply_json = dict()
                reply_json["components"] = None
                try:
                    verb = mlist[1]
                    subject = mlist[2]
                    if subject not in os.listdir( "hw" ):
                        print( f"{ subject } not in { subjects }" )
                        for i in subjects:
                            print( f"Checking {i}" )
                            assignments = os.listdir( f"hw/{ i }" )
                            print( assignments )
                            try:
                                if subject in assignments:
                                    print( f"Found { subject } in { i }" )
                                    assignment = subject
                                    subject = i
                                    person = mlist[3]
                                    print( "Could assign person" )
                                    rating = mlist[4]
                                    print( "Could assign rating" )
                                    break
                                else:
                                    print( f"{subject} not in { assignments }" )
                            except Exception as e:
                                print( f"[red]Should not be here cuz {e}" )
                                print( "Not enough args for rate, pull or push" )
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
                            with open( f"hw/{ subject }/{ assignment }/{message['author']['username']}.pdf", "wb") as f:
                                f.write( r.content )
                            ratings = json.load( open( f"hw/{ subject }/{ assignment }/.ratings.json" ) )
                            ratings[ message[ "author" ][ "username"] ] = { "ratings" : [] }
                            reply_json["content"] = "Recieved! Thank you!"
                        except IndexError as e:
                            reply_json["content"] = "Not enough arguments (probably) "

                    case "pull" | "get" :
                        if "person" not in locals():
                            ratings = json.load( open( f"hw/{ subject }/{ assignment }/.ratings.json" ) )
                            
                            max_rating = { "rate_value" : 0 }
                            print( ratings )
                            for i in ratings.keys():
                                if i == "Name":
                                    continue
                                if ratings[i]["rate_value"] > max_rating["rate_value"] :
                                    max_rating = ratings[i]
                                    person = i
                            api_post( f"channels/{channel_id}/messages", None, files= { "hw.pdf" : open( f"hw/{ subject }/{ assignment }/{ person }.pdf", "rb" )}  )
                            send_reply = False
                            
                        elif os.path.exists( f"hw/{ subject }/{ assignment }/{ person }.pdf" ):
                            reply_json["content"] = "Here you go"
                            api_post( f"channels/{channel_id}/messages", None, files= { "hw.pdf" : open( f"hw/{ subject }/{ assignment }/{ person }.pdf", "rb" )}  )
                            send_reply = False
                        else:
                            reply_json["content"] = "Syntax incorrect"

                    case "list" | "ls" : 
                        try:
                            if  "subject" not in locals(): #List subjects
                                reply_json["content"] = ", ".join( subjects ) 
                            elif  "assignment" not in locals(): #List assignments
                                for i in subjects:
                                    reply_json["content"] = ", ".join( os.listdir( f"hw/{ i }" ) )
                            elif "person" not in locals(): #List files
                                msg_draft = ""
                                
                                ratings = json.load( open( f"hw/{ subject }/{ assignment }/.ratings.json" ) )
                                for i in ratings.keys():
                                    try:
                                        msg_draft += f"{ i }:\t { ratings[ i ][ 'rate_value' ] }\n"
                                    except:
                                        msg_draft += f"Assignment: { ratings[ i ] }\n\n"
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
                        voice_channel_id = ""
                        for i in resp:
                            if i["type"] == 2:
                                print( f"Voice channel { i[ 'name' ] }" )
                                reply_json["content"] = f"Joining voice channel { i[ 'name' ] }!"
                                voice_channel_id = i[ "id" ]
                        await shared_info.put( draft( VOICE_CONNECT, guild=message["guild_id"], channel=voice_channel_id ) )
                    
                    case "leave":
                        reply_json["content"] = "Leaving..."
                        await shared_info.put( draft( VOICE_CONNECT, guild=message["guild_id"] ) )
                    case _:
                        reply_json["content"] = f"Invalid verb, use hw pull to get hw, pulling without verb will be added soon"
                            

                
                if send_reply:
                    print( reply_json )
                    print( api_post( f"channels/{channel_id}/messages", reply_json ).content )
                else:
                    send_reply = True
