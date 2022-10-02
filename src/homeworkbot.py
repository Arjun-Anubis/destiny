#!/bin/python3.11
# local
from header import *
from exceptions import HardReset, SoftReset
from convenience import api_post, draft
import default_handlers

import opus

import asyncudp


# rich

from rich import inspect
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.traceback import install


# pip installed 
import requests
import nacl.secret as secret
import pyaudio as pyaudio
import ctypes
import asyncio
import wave
                    
# system

import uuid
import socket
import random
import os.path
import os
import sys
import websockets
import json
import traceback
 


# p = pyaudio.PyAudio()
# stream2 = p.open( format=pyaudio.paFloat32, channels=2, rate=48000, output=True )
# stream = open( "output.raw", "rb" )

install()

        
class Client():
    def __init__( self, msg_handler=default_handlers.message_handler, cg_handler=default_handlers.cg_handler, misc_handler=default_handlers.misc_handler ):
        self.message_handler = msg_handler
        self.cg_handler = cg_handler
        self.misc_handler = misc_handler
        
    def run( self ):
        while True:
            try:
                asyncio.run( self.main( "wss://gateway.discord.gg" ) )
            except HardReset as e:
                print ( "Caught hard reset!" )
                break
            except SoftReset as e:
                print ( "Soft reset" )
            except KeyboardInterrupt:
                print( "[green] Closing to keyboard interrupt" )
                quit()
            except Exception as e:
                raise e

    async def main( self, url ):
        shared_info = asyncio.Queue( 30 )
        voice_info = asyncio.Queue( 30 )
        async with websockets.connect(url) as websocket:
            main_websocket_task = asyncio.create_task( self.websoc_main( websocket, shared_info, voice_info ) )
            await main_websocket_task
            print ( "All done!" )
    
    async def websoc_main( self, websocket, shared_info, voice_info ):

        await websocket.send( draft( IDENTIFY ) )
        raw = await websocket.recv()
        op10 = json.loads( raw )
        
        # print ( op10 )
        if op10[ "op" ] == 10:
           hbi = op10[ "d" ][ "heartbeat_interval" ] 
        
        raw = await websocket.recv()
        ready = json.loads( raw )

        # print ( ready )

        if ready[ "op" ] == 0 and ready[ "t" ] == "READY":
            session_info = dict()
            session_info[ "session_id" ] = ready["d"][ "session_id" ]
            session_info[ "user" ] = ready[ "d" ][ "user" ]

        websoc_handler_task = asyncio.create_task( self.websoc_handler( websocket, session_info, shared_info, voice_info ) )
        send_task = asyncio.create_task( self.send( websocket, shared_info ) )
        heart_beat_task = asyncio.create_task( self.heart_beat( websocket, hbi ) )
        voice_main_task = asyncio.create_task( self.voice( session_info, voice_info ) )
        
        await websoc_handler_task
        await send_task
        await heartbeat_task
        await voice_main_task

        print ( "All done with main websoc" )

    async def websoc_handler( self, websocket, session_info, shared_info, voice_info ):
        while True:
            raw =  await websocket.recv()
            js = json.loads( raw )

            match js["op"]:
                case 0:
                    match js[ "t" ]:

                        case "MESSAGE_CREATE":
                            await self.message_handler( js, shared_info, voice_info, **session_info ) 

                        case "VOICE_SERVER_UPDATE":
                            print ( js )
                            voice_update = dict()
                            voice_update[ "voice_url" ] = f'wss://{ js[ "d" ][ "endpoint" ] }'
                            voice_update[ "voice_guild_id" ] = js[ "d" ][ "guild_id" ]
                            voice_update[ "voice_token" ] = js[ "d" ][ "token" ]
                            await voice_info.put( voice_update )
                        case "GUILD_CREATE":
                            await self.cg_handler( js, shared_info, voice_info, **session_info ) 
                               
                        case _:
                            await self.misc_handler( js, shared_info, voice_info, **session_info ) 
                            
                case 11:
                    # print ( "[cyan bold]Heartbeat: " )
                    # print ( js )
                    pass
                case _:
                    print (js)
    async def send( self, websocket, shared_info ):
        while True:
            buffer_send = await shared_info.get()
            await websocket.send( buffer_send )

    async def heart_beat( self, websocket, hbi ):
        while True:
            await websocket.send( json.dumps( { "op" : 1, "d" : None  } ) )
            await asyncio.sleep( hbi / 1000 )

    async def voice( self, session_info, voice_info ):
        voice_update = await voice_info.get()
        async with websockets.connect( voice_update[ "voice_url" ] + "?v=4" ) as voice_socket:
            try:
                js = json.loads( await voice_socket.recv() )
                if js[ "op" ] == 8:
                    resp = json.dumps( { "op" : 0, "d" : { "server_id" : voice_update[ "voice_guild_id" ], "user_id" : session_info[ "user" ][ "id" ], "session_id" : session_info[ "session_id" ], "token" : voice_update[ "voice_token" ] } } )
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

            except websockets.ConnectionClosed as e:
                inspect ( e )
            

    async def voice_beat( self, voice_socket, voicebeat_interval ):
        while True:
            resp =  json.dumps( { "op" : 3, "d" : uuid.uuid4().int } )
            # print ( "[cyan bold]Sending: " )
            # print ( resp )
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
                    # print ( "[cyan bold]Recieved: " )
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
        recv_port = int.from_bytes( data[-2:] )

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
