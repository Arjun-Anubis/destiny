import asyncore
import asyncio
import logging
import socket

class Client( asyncore.dispatcher ):
    
    def __init__( self, host ):
        self.logger = logging.getLogger()
        asyncore.dispatcher.__init__( self )
        self.create_socket( socket.AF_INET, socket.SOCK_DGRAM )
        self.connect( ( host, 9999 ) )
    def writeable( self ):
        print( "writable" )


async def  main():
    a = Client( "127.0.0.1" )

asyncio.run( main() )
