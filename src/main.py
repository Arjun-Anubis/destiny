import destiny
import destiny.core as core
import destiny.default_handlers as default_handlers
import destiny.message_handler as message_handler
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

        if ( me.id == author.id ):
            return
        
        f1= compile( prefix + "{verb}" )
        f2= compile( prefix + "{verb} {arg1}" )
        f3= compile( prefix + "{verb} {arg1} {arg2}" )
        
        contents = message.content

        singular = f1.parse( contents )
        dual = f2.parse( contents )
        ternary = f3.parse( contents )

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



        


client = custom_client( )
destiny.runners.auto_reload(client)
