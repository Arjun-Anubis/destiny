#!/bin/python3.11
# local
from destiny.header import *
from destiny.exceptions import *
import destiny.header as header
import destiny.structs as structs
import destiny.events as events
import destiny.objects as objects


import opus



# rich

# pip installed 
import requests
import nacl.secret as secret
import pyaudio as pyaudio
import ctypes
import wave
import jsons
import websocket

# system

import time
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
import threading
import queue




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
        return [ objects.Channel( channel ) for channel in resp.json() ]

    def join_voice_channel( self, guild_id, channel: objects.Channel, **kwargs ) -> structs.Result:
        self._event_send( events.Update_Voice_State( data = events.Voice_State( guild_id=guild_id, channel=channel, **kwargs)._dict  ) )

    def leave_voice_channel( self, guild_id, **kwargs ) -> structs.Result:
         self._event_send( events.Update_Voice_State( data = events.Voice_State( guild_id=guild_id, channel=None, **kwargs)._dict  ) )

    def _api_post( self, subdivision, method="POST", **kwargs ): # add post to constants
        try:
            log.debug( f"Sending payload { kwargs['data'] } to {rest_url}{subdivision} as {method}" )
        except:
            log.debug( f"Requesting {rest_url}{subdivision} with {method}" )
        return requests.request( method,  f"{rest_url}{subdivision}", headers=header._header_gen(self.config.token), **kwargs )

    def on_message( self, message : objects.Message ):
        pass
    def on_guild_create( self, dispatch ): #
        pass
    def on_unimplimented( self ):
        pass

    def _on_dispatch( self, dispatch : events.Dispatch ):
        """
        Handle Dispatch
        Override at your own risk
        """
        match dispatch.type:

            case "MESSAGE_CREATE":
                message = objects.Message( **dispatch.data )
                self.on_message( message )

            case "VOICE_SERVER_UPDATE":
                voice_update = {
                        "voice_url" : f"wss://{ dispatch.data['endpoint'] }",
                        "voice_guild_id" : dispatch.data["guild_id"],
                        "voice_token" : dispatch.data["token"]
                        }
                self._voice_clients.append( VoiceClient( self, voice_update ) )
                log.info( "back to sync" )


            case "GUILD_CREATE":
                self.on_guild_create( dispatch )
            case "VOICE_STATE_UPDATE":
                log.warning( "Unhandled Voice State update" )
                log.warning( dispatch )

                """
                In principle, the VOICE_STATE_UPDATE should be used to determine the session_id, but it appears to be the same as self.session_id, 
                Thus, will change to handle later
                """
                # pass

            case _:
                log.warning( f"Unimplimented: {dispatch.type}" )
                self.on_unimplimented( )

    def run( self ):
        while True:
            try:
                # io.run( self._initialize_async( "wss://gateway.discord.gg" ) )
                self._initialize( "wss://gateway.discord.gg" )
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
        # io.run( self._initialize_async( "wss://gateway.discord.gg" ) )

    def _initialize( self, url ):

        log.info("[green]Initializing IPC..." )

        self._event_queue = queue.Queue(30)
        self.heartbeat = queue.Queue(1)
        self._voice_clients = []
        self.session = {}


        self._websocket = websocket.create_connection( url ) 
        log.info( "[yellow]Initializing websocket" )

        # Create class structure TODO
        hello_event = events.Hello( **json.loads( self._websocket.recv() ) )

        assert hello_event.opcode == 10
        heartbeat_interval = hello_event.data.heartbeat_interval
        del hello_event


        log.info( "[yellow]Identifying..." )
        identify_message = events.Identify( self.config ) 
        self._websocket.send( identify_message.pack() )

        ready = events.Ready( json.loads( self._websocket.recv() ) )
        if ready.opcode == 0 and ready.type == "READY":
            log.info( "[green]Done!" )
            self.session = structs.Structure( ready.data )
        log.info(ready)
        del ready
        

        #     results = io.gather( self._event_handler_d(), self._sender_d(), self._heartbeat_d( heartbeat_interval ), return_exceptions=False )
        event_handler = threading.Thread( target=self._event_handler_d  )
        sender = threading.Thread( target=self._sender_d)
        heartbeater = threading.Thread( target=self._heartbeat_d, args=(heartbeat_interval,) )

        event_handler.start()
        sender.start()
        heartbeater.start()

        event_handler.join()
        sender.join()
        heartbeater.join()


        self._websocket.close()

    def _event_handler_d( self ):

         while True:
            event = json.loads(  self._websocket.recv() )


            match event["op"]:
                case 0:
                    """
                    Dispatch
                    """
                    dispatch = events.Dispatch( **event )
                    self._on_dispatch( dispatch )

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
                    self.heartbeat.put(event)

                    pass
                case _:
                    log.error("Unrecognised op code")
                    raise UnkownOpcode

    def _sender_d( self ): # legacy
         while True:
            self._websocket.send( self._event_queue.get() )
            log.info( "Sent message from queue" )

    def _event_send( self, event: events.send_event ):  #one shot
        """
        Function to allow synchronous functions to send events, using a queue
        """
        return  self._event_queue.put( event.pack() )

    def _heartbeat_d( self, heartbeat_interval ):
        while True:
            log.debug("[yellow]Sending heartbeat")

            heartbeat = events.Heartbeat()
            log.info( "[yellow]Lub...?" )
            self._websocket.send( heartbeat.pack() )

            heartbeat_acknowledge =  self.heartbeat.get()
            log.debug("[green]Received acknowledgement on queue, waiting...")
            log.info( "[green]...Dub!" )


            jitter = random.random()
            time.sleep( jitter * (heartbeat_interval / 1000) )

class VoiceClient:
    def __init__( self, parent, voice_update ):
        self.parent = parent
        io.as_completed(( self._voice_sd( voice_update ) ))

    def _voice_sd( self, voice_update  ):
         log.info( "Voice sd" )
         with websockets.connect( voice_update[ "voice_url" ] + "?v=4" ) as self._voicesocket:
             # Voice socket cycle

            dispatch = events.Dispatch_v( json.loads(  self._voicesocket.recv() ) )

            match dispatch.opcode:
                case 8:

                    identify = events.Identify_v(
                            events.config_identify_v( 
                                token=voice_update.voice_token,
                                server_id=voice_update.voice_guild_id,
                                user_id=self.session.user.id,
                                session_id=self.session.session_id ) 
                            )

                    log.info( f"Sending => {identify.pack()}" )
                    self._voicesocket.send( identify.pack() )

                    # op2 =  voice_socket.recv()
                    # op2 = json.loads( op2 )

                    ready = events.Ready_v( json.loads( self._voicesocket.recv()) )
                    assert ready.opcode == 2

                    log.info( ready )

                    self.voice_send_info = io.Queue( 30 )
                    self.voice_recv_info = io.Queue( 30 )
                    self.heartbeat = io.Queue( 1 )

                    voice_send_task = io.create_task( self.voice_send( ) )
                    voice_udp_task = io.create_task( self.voice_udp( ready ) )
                    voice_handle_task = io.create_task( self.voice_handle() )
                    voice_beat_task = io.create_task( self.voice_beat( dispatch.data.heartbeat_interval ) )
                    #  voice_beat_task
                    #  voice_handle_task
                    #  voice_send_task
                    #  voice_udp_task




    def voice_beat( self, heartbeat_interval ):
         while True:
             # resp =  json.dumps( { "op" : 3, "d" : uuid.uuid4().int } )
            #  voice_socket.send( resp )
            #  io.sleep( voicebeat_interval/1000 )

            log.debug("[yellow]Sending [orange]voicebeat")

            heartbeat = events.Heartbeat_v()
            log.info( "[blue]Lub...?" )
            self._voicesocket.send( heartbeat.pack() )

            heartbeat_acknowledge =  self.heartbeat.get()
            log.info("[purple]Received acknowledgement on queue, checking nonce...")

            assert heartbeat.data == heartbeat_acknowledge.data

            log.info( "[pink]...Dub!" )


            jitter = random.random()
            time.sleep( jitter * (heartbeat_interval / 1000) )

    def voice_handle( self, voice_socket, voice_recv_info ):
         while True:
            dispatch = events.Dispatch( json.loads(  self._voicesocket.recv() ) )
            match dispatch.opcode:
                case 4:
                    self.voice_recv_info.put( js )
                case 6:
                    self.heartbeat.put( dispatch )
                case _:
                    print ( js )

    
    def voice_send( self, voice_socket, voice_send_info ):
         while True:
            buffer_send =  voice_send_info.get()
            print ( buffer_send )
            voice_socket.send( buffer_send ) 


    def voice_udp( self, ip, port, ssrc, voice_send_info, voice_recv_info ):

        while True:
            voice_socket =   udp.create_socket( remote_addr = ( ip, port ) )
            if voice_socket._protocol._is_ready:
                print ( voice_socket._protocol._is_ready )
                break
            else:
                print ( "[red bold]Connection refused... Re-trying in 5..." )
                time.sleep( 5 )
                continue

        discovery = bytes.fromhex( "00010046" ) + int.to_bytes( ssrc, 4, "big" ) + int.to_bytes( 0, 66, "big" )
        voice_socket.sendto(discovery) 

        data, addr =  voice_socket.recvfrom()
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


        voice_send_info.put( json.dumps( repl ) )

        data, addr =  voice_socket.recvfrom()

        repl =  voice_recv_info.get()
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
        voice_send_info.put( json.dumps ({ "op" : 5, "d" : { "speaking": 5, "delay" : 0, "ssrc" : int.from_bytes( send_ssrc ) } } ) ) 
        f = open( "test.raw", "wb" )

        with Live( "recieving" ) as live:
            while True:

                try:
                    data, addr =  voice_socket.recvfrom()
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

