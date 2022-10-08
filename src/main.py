import destiny
import destiny.core as core
import destiny.runners
from destiny.header import *
from destiny.structs import *

import os


from parse import *
from parse import compile
# client = core.Client( message_handler.message_handler )

prefix = "hw"
subjects = os.listdir( DEST_DIR )

class custom_client( core.Client ):
    async def on_message( self, message ):
        author = User( **message.author )
        me = User( **self.session["user"] )
        # inspect( me, private=True )

        log.info( f"{author.username}: {message.content}" )
        if ( me.id == author.id ):
            return
        
        f1= compile( prefix + "{verb}" )
        f2= compile( prefix + "{verb} {arg1}" )
        f3= compile( prefix + "{verb} {arg1} {arg2}" )
        f4= compile( "ping" )
        
        contents = message.content

        singular = f1.parse( contents )
        dual = f2.parse( contents )
        ternary = f3.parse( contents )

        if f4.parse( contents ):
            log.info( self.message( message.channel_id, Message( content="Pong!" )  ) )


        if ternary:
            verb = ternary.named["verb"].strip()
            arg1 = ternary.named["arg1"].strip()
            arg2 = ternary.named["arg2"].strip()


            if search( "ls", verb ):
                log.info( "Matched ls (ternary)" )

                # running special check for files

                try:
                    files = os.listdir( f"{DEST_DIR}/{arg1}/{arg2}" )
                except:
                    self.message( message.channel_id, Message( content="Sorry, We are unable to find that assignment" ) )
                    return
                self.message( message.channel_id, Message( content=files.__str__()) )
            elif search( "pull", verb ):
                log.info( "Matched pull (ternary)" )
                self.message( message.channel_id, Message( content="Here you go" ), files={ "anubi.pdf" : open( f"{DEST_DIR}/{arg1}/{arg2}/anubi.pdf" ) } ) 

        elif dual:
            verb = dual.named["verb"].strip()
            arg1 = dual.named["arg1"].strip()

            log.info( f"Matched dual verb, verb is { verb }, argument is { arg1 }" )

            if search( "ls", verb ):
                log.info( "Matched ls (dual)" )

                # running special check for subject

                log.info( f"Looking in {DEST_DIR}/{arg1}." )
                try:
                    assignments = os.listdir( f"{DEST_DIR}/{arg1}" )
                except:
                    self.message( message.channel_id, Message( content="Sorry, We are unable to find that subject" ) )
                    return
            


                self.message( message.channel_id, Message( content=assignments.__str__()) )

        elif singular:
            verb = singular.named["verb"].strip()

            log.info( f"Matched singular verb, verb is { verb }" )
            if search( "ls", verb ):
                log.info( "Matched ls (singular)" )

                channel_id = message.channel_id
                draft = Message( content=subjects.__str__() )
                self.message( channel_id, draft )
            elif search( "join", verb ):
                log.info( "Matched join (singular)" )

                voice_channels = [ channel for channel in self.query_channels( message.guild_id ) if channel.type == 2 ]

                log.info( f"Voice Channels")

                selected_channel = voice_channels[0]
                log.info( selected_channel )
                self.message( message.channel_id, Message( content=f"Joining {str(selected_channel)}" ) )
                await self.join_voice_channel( message.guild_id, selected_channel, self_mute=True )
            elif search("leave", verb):
                await self.leave_voice_channel( message.guild_id, self_mute=True )


    async def on_guild_create( self, dispatch ):
        log.info( f"[green]{ self.session['user']['username'] } is Online!" )


        

config = config_identify( token=token, intents=641, properties=network_properties( os="linux" ) ) 
client = custom_client( config )
destiny.runners.auto_reload(client)
