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


        if singular:
            primary = singular.named["verb"]

            log.info( f"Matched singular verb, primary is { primary }" )
            if search( "ls", primary ):
                log.info( "Matched ls (singular)" )
                channel_id = message.channel_id
                draft = Message( content=subjects.__str__() )
                log.info( draft.content )
                self.message( channel_id, draft )


        


client = custom_client( )
destiny.runners.auto_reload(client)
