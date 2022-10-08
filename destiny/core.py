#!/bin/python3.11
# local
from destiny.header import *
from destiny.exceptions import *
import destiny.header as header
import destiny.structs as structs


import opus

import destiny.asyncudp as asyncudp


# rich

# pip installed 
import requests
import nacl.secret as secret
import pyaudio as pyaudio
import ctypes
import asyncio
import wave
                    
# system

import random
import logging
import uuid
import socket
import random
import os.path
import os
import sys
import websockets
import json
import traceback
 


        
class Client():
    def __init__( self, config ):
        """
        A client object is an instance of the discord bot, derive with the methods on_message, on_guild_create etc.
        """
        self.config = config


    def message( self, channel_id, message, **kwargs):
        return self._api_post( f"channels/{channel_id}/messages", data=message, **kwargs)

    def query_channels( self, guild_id, **kwargs):
        resp =  self._api_post( f"guilds/{ guild_id }/channels", method="GET" )
        log.info( resp )
        return [ structs.Channel( channel ) for channel in resp.json() ]

    async def join_voice_channel( self, guild_id, channel: structs.Channel, **kwargs ) -> structs.Result:
        await self._event_send( structs.Update_Voice_State( data = structs.Voice_State( guild_id=guild_id, channel=channel, **kwargs)._dict  ) )

    async def leave_voice_channel( self, guild_id, **kwargs ) -> structs.Result:
        await self._event_send( structs.Update_Voice_State( data = structs.Voice_State( guild_id=guild_id, channel=None, **kwargs)._dict  ) )

    def _api_post( self, subdivision, method="POST", **kwargs ): # add post to constants
        try:
            log.debug( f"Sending payload { kwargs['data'] } to {rest_url}{subdivision} as {method}" )
        except:
            log.debug( f"Requesting {rest_url}{subdivision} with {method}" )
        return requests.request( method,  f"{rest_url}{subdivision}", headers=header._header_gen(self.config.token), **kwargs )

    async def on_message( self, message : structs.Message ):
        pass
    async def on_guild_create( self, dispatch ): #
        pass
    async def on_unimplimented( self ):
        pass
        
    async def _on_dispatch( self, dispatch : structs.Dispatch ):
        """
        Handle Dispatch
        Override at your own risk
        """
        match dispatch.type:

            case "MESSAGE_CREATE":
                message = structs.Message( **dispatch.data )
                await self.on_message( message )

            case "VOICE_SERVER_UPDATE":
                voice_update = {
                        "voice_url" : f"wss://{ dispatch.data['endpoint'] }",
                        "voice_guild_id" : dispatch.data["guild_id"],
                        "voice_token" : dispatch.data["token"]
                        }
                await self._voice_sd( voice_update )
                log.info( "back to sync" )


            case "GUILD_CREATE":
                await self.on_guild_create( dispatch )
            case "VOICE_STATE_UPDATE":
                pass
                   
            case _:
                log.warning( f"Unimplimented: {dispatch.type}" )
                await self.on_unimplimented( )

    def run( self ):
        while True:
            try:
                asyncio.run( self._initialize_async( "wss://gateway.discord.gg" ) )
            except HardReset as e:
                log.critical("Hard Reset")
                break
            except SoftReset as e:
                log.warning( "Soft reset" )
            except KeyboardInterrupt:
                print( "[green] Closing to keyboard interrupt" )
                quit()
            except Exception as e:
                raise e
        # asyncio.run( self._initialize_async( "wss://gateway.discord.gg" ) )

    async def _initialize_async( self, url ):

        log.info("[green]Initializing IPC..." )

        self._event_queue = asyncio.Queue(30)
        self._voice_queue = asyncio.Queue(30)
        self.heartbeat = asyncio.Queue(1)
        self.session = {}


        async with websockets.connect(url, ping_timeout=None, ping_interval=None) as self._websocket:
                log.info( "Initializing websocket" )

                # Create class structure TODO
                hello_event = structs.Hello( **json.loads( await self._websocket.recv() ) )
                log.info(hello_event)
                
                assert hello_event.opcode == 10
                heartbeat_interval = hello_event.data.heartbeat_interval
                del hello_event


                log.info( "[yellow]Identifying..." )
                identify_message = structs.Identify( self.config ) 
                await self._websocket.send( identify_message.pack() )

                ready = structs.Ready( json.loads( await self._websocket.recv() ) )
                if ready.opcode == 0 and ready.type == "READY":
                    log.info( "[green]Done!" )
                    # print( ready )
                    self.session = {
                            "session_id" : ready.data.session_id,
                            "user" : ready.data.user
                            }
                del ready

                try:
                    results = await asyncio.gather( self._event_handler_d(), self._sender_d(), self._heartbeat_d( heartbeat_interval ), return_exceptions=False )
                except Exception as e:
                    raise e

    async def _event_handler_d( self ):

        while True:
            event = json.loads( await self._websocket.recv() )


            match event["op"]:
                case 0:
                    """
                    Dispatch
                    """
                    dispatch = structs.Dispatch( **event )
                    await self._on_dispatch( dispatch )
                            
                case 7:
                    """
                    Reconnect
                    """
                    log.warning("Reconnecting because server said so")
                case 9:
                    """
                    Session Invalid
                    """
                    log.error("Session Invalid")
                    raise SessionInvalid
                case 10:
                    """
                    Hello

                    Shouldnt be sent after first connect,
                    """
                    log.error( "Should not receive this, hello after connection established" )
                    raise ErrOpcode
                case 11:
                    """
                    Heart beat acknowledged
                    """
                    log.debug( "[cyan bold]Putting acknowledge on queue" )
                    await self.heartbeat.put(event)

                    pass
                case _:
                    log.error("Unrecognised op code")
                    raise UnkownOpcode

    async def _sender_d( self ): # legacy
        while True:
            await self._websocket.send( await self._event_queue.get() )
            log.info( "Sent message from queue" )

    async def _event_send( self, event: structs.send_event ):  #one shot
        """
        Function to allow synchronous functions to send events, using a queue
        """
        return await self._event_queue.put( event.pack() )

    async def _heartbeat_d( self, heartbeat_interval ):
        while True:
            log.debug("[yellow]Sending heartbeat")

            heartbeat = structs.Heartbeat()
            log.info( "[yellow]Lub...?" )
            await self._websocket.send( heartbeat.pack() )

            heartbeat_acknowledge = await self.heartbeat.get()
            log.debug("[green]Received acknowledgement on queue, waiting...")
            log.info( "[green]...Dub!" )


            jitter = random.random()
            await asyncio.sleep( jitter * (heartbeat_interval / 1000) )

    async def _voice_sd( self, voice_update  ):
        async with websockets.connect( voice_update[ "voice_url" ] + "?v=4" ) as voice_socket:
            # Voice socket cycle


            js = Dispatch_v( json.loads( await voice_socket.recv() ) )



            match js["op"]:
                case 8:
                    resp = json.dumps( { "op" : 0, "d" : { "server_id" : voice_update[ "voice_guild_id" ], "user_id" : self.session[ "user" ][ "id" ], "session_id" : self.session[ "session_id" ], "token" : voice_update[ "voice_token" ] } } )
                    await voice_socket.send( resp )
                    op2 = await voice_socket.recv()
                    op2 = json.loads( op2 )
                    voice_send_info = asyncio.Queue( 30 )
                    voice_recv_info = asyncio.Queue( 30 )
                    voice_send_task = asyncio.create_task( self.voice_send( voice_socket, voice_send_info ) )
                    voice_udp_task = asyncio.create_task( self.voice_udp( op2["d"]["ip"], op2["d"]["port"] , op2["d"]["ssrc"], voice_send_info, voice_recv_info ) )
                    voice_handle_task = asyncio.create_task( self.voice_handle( voice_socket, voice_recv_info ) )
                    voice_beat_task = asyncio.create_task( self.voice_beat( voice_socket , js[ "d" ][ "heartbeat_interval" ] ) )
                    # await voice_beat_task
                    # await voice_handle_task
                    # await voice_send_task
                    # await voice_udp_task

            


    async def voice_beat( self, voice_socket, voicebeat_interval ):
        while True:
            resp =  json.dumps( { "op" : 3, "d" : uuid.uuid4().int } )
            await voice_socket.send( resp )
            await asyncio.sleep( voicebeat_interval/1000 )
        
    async def voice_handle( self, voice_socket, voice_recv_info ):
        while True:
            try:
                js = json.loads( await voice_socket.recv() )
            except Exception as e:
                inspect( e )
                raise e
            match js[ "op" ]: 
                case 4:
                    await voice_recv_info.put( js )
                case _:
                    print ( js )

    async def voice_send( self, voice_socket, voice_send_info ):
        while True:
            buffer_send = await voice_send_info.get()
            print ( buffer_send )
            await voice_socket.send( buffer_send ) 

                        
    async def voice_udp( self, ip, port, ssrc, voice_send_info, voice_recv_info ):
        
        while True:
            voice_socket = await  asyncudp.create_socket( remote_addr = ( ip, port ) )
            if voice_socket._protocol._is_ready:
                print ( voice_socket._protocol._is_ready )
                break
            else:
                print ( "[red bold]Connection refused... Re-trying in 5..." )
                await asyncio.sleep( 5 )
                continue
        



        discovery = bytes.fromhex( "00010046" ) + int.to_bytes( ssrc, 4, "big" ) + int.to_bytes( 0, 66, "big" )
        voice_socket.sendto(discovery) 

        data, addr = await voice_socket.recvfrom()
        recv_ip = "".join([ chr( i )  for i in data[8:50] if i !=b'0x00' ])
        recv_port = int.from_bytes( data[-2:] , "big" )

        repl = dict()
        repl["op"] = 1
        repl["d"] = dict()
        repl["d"]["protocol"] = "udp"
        repl["d"]["data"] = dict()
        repl["d"]["data"]["address"] = recv_ip
        repl["d"]["data"]["port"] = recv_port
        repl["d"]["data"]["mode"] = "xsalsa20_poly1305"


        await voice_send_info.put( json.dumps( repl ) )

        data, addr = await voice_socket.recvfrom()

        repl = await voice_recv_info.get()
        # ssrc = repl["d"]["ssrc"]
        key =  bytes( repl["d"]["secret_key"] ) 
        print (len(key))
        safe = secret.SecretBox( key )
        
        decoder = opus.decoder.Decoder( 48000, 2 )
        encoder = opus.encoder.Encoder( 48000, 2, 2049 )
        send_sequence = 0
        sequence = 0
        send_ssrc = os.urandom(4)
        send_time = 0
        await voice_send_info.put( json.dumps ({ "op" : 5, "d" : { "speaking": 5, "delay" : 0, "ssrc" : int.from_bytes( send_ssrc ) } } ) ) 
        f = open( "test.raw", "wb" )

        with Live( "recieving" ) as live:
            while True:
                    
                try:
                    data, addr = await voice_socket.recvfrom()
                except Exception as e:
                    inspect( e )
                print( sequence )
                print ( "." )
                td = ""
                
                if data[0] == 129:
                    td += ("[red bold]Silence\n") 
                    live.update(td)
                    continue
                elif data[0] == 128:

                    td += ( "[green bold]Voice\n")

                    sequence = data[2:4]
                    time_stamp = data[4:8]
            
                    nonce = bytearray(24)
                    nonce[:12] = data[:12] # Setting nonce from header
                    encrypted_data = data[12:]

                    decrypted_data = safe.decrypt( bytes( encrypted_data ), bytes( nonce ) ) 

                    decoded_data = decoder.decode( decrypted_data, 960 )
                    print( decoded_data )
                    f.write( decoded_data )
            
                send_header = bytearray( 12 )
                send_header[0] = 0x80
                send_header[1] = 0x78
                send_header[2:4] = send_sequence.to_bytes(2, "big" )
                send_header[4:8] = send_time.to_bytes(4, "big" )
                send_header[8:12] = send_ssrc
                send_nonce = send_header + bytearray(12)
                send_to_be_encoded = stream.read( 1920 )
                print( len ( send_to_be_encoded ) )
                if len( send_to_be_encoded ):
                    send_data = send_header + safe.encrypt( encoder.encode( send_to_be_encoded, 960 ), bytes( send_nonce ) ) 
                else:
                    print ( "Over" )
                
                
            
                voice_socket.sendto( send_data )
                send_sequence += 1
                send_time += 20
                td += f"[purple]Length: [cyan]\n[/cyan purple]"
                live.update(td)


        voice_socket.close()

