import destiny.core as core
import destiny.audio as audio
from destiny.header import *
from destiny.structs import *
from destiny.events import *
from destiny.objects import *

import os
import pyogg
import dotenv

dotenv.load_dotenv()


import parse
from parse import compile
# client = core.Client( message_handler.message_handler )

destdir = "assets/hw"
prefix = "hw"
subjects = os.listdir( destdir )

class custom_client( core.Client ):
    def on_message( self, message ):
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


            if parse.search( "ls", verb ):
                log.info( "Matched ls (ternary)" )

                # running special check for files

                try:
                    files = os.listdir( f"{destdir}/{arg1}/{arg2}" )
                except:
                    self.message( message.channel_id, Message( content="Sorry, We are unable to find that assignment" ) )
                    return
                self.message( message.channel_id, Message( content=files.__str__()) )
            elif parse.search( "pull", verb ):
                log.info( "Matched pull (ternary)" )
                self.message( message.channel_id, Message( content="Here you go" ), files={ "anubi.pdf" : open( f"{destdir}/{arg1}/{arg2}/anubi.pdf" ) } ) 

        elif dual:
            verb = dual.named["verb"].strip()
            arg1 = dual.named["arg1"].strip()

            log.info( f"Matched dual verb, verb is { verb }, argument is { arg1 }" )

            if parse.search( "ls", verb ):
                log.info( "Matched ls (dual)" )

                # running special check for subject

                log.info( f"Looking in {destdir}/{arg1}." )
                try:
                    assignments = os.listdir( f"{destdir}/{arg1}" )
                except:
                    self.message( message.channel_id, Message( content="Sorry, We are unable to find that subject" ) )
                    return
            


                self.message( message.channel_id, Message( content=assignments.__str__()) )

        elif singular:
            verb = singular.named["verb"].strip()

            log.info( f"Matched singular verb, verb is { verb }" )
            if parse.search( "ls", verb ):
                log.info( "Matched ls (singular)" )

                channel_id = message.channel_id
                draft = Message( content=subjects.__str__() )
                self.message( channel_id, draft )
            elif parse.search( "join", verb ):
                log.info( "Matched join (singular)" )

                voice_channels = [ channel for channel in self.query_channels( message.guild_id ) if channel.type == 2 ]

                log.debug( f"Voice Channels")

                selected_channel = voice_channels[0]
                log.debug( selected_channel )
                self.message( message.channel_id, Message( content=f"Joining {str(selected_channel)}" ) )
                self.join_voice_channel( message.guild_id, selected_channel, self_mute=True )
            elif parse.search("leave", verb):
                self.leave_voice_channel( message.guild_id, self_mute=True )
            elif parse.search("speak", verb):
                client = self._voice_clients[0]
                client.cmd.put( lambda: client._set_speak( mic=True, priority= True ) )
            elif parse.search("play", verb):
                client = self._voice_clients[0]
                source = pyogg.OpusFileStream("assets/audio.opus")
                client.cmd.put( lambda: client.play( source ) )


    def on_guild_create( self, dispatch ):
        log.info( f"[green]{ self.session['user']['username'] } is Online!" )


        

config = config_identify( token=os.environ["token"], intents=641, properties=network_properties( os="linux" ) ) 
client = custom_client( config )
client.run()
# destiny.runners.auto_reload(client)
