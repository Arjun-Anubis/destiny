#!/bin/python3.11
# local
from destiny.header import *
from destiny.exceptions import *
import destiny.header as header
import destiny.structs as structs
import destiny.events as events
import destiny.objects as objects
import destiny.audio as audio



# pip installed 
import requests
import websocket
from contextlib import closing

# system

import os
import time
import random
import json
import threading
import queue

from rich.traceback import install

install()


class Client():
    def __init__( self, config ):
        """
        A client object is an instance of the discord bot, derive with the methods on_message, on_guild_create etc.
        """
        self.config = config


    def message( self, channel_id, message, **kwargs):
        """
        Post a message to a channel, given a channel id
        """
        return self._api_post( f"channels/{channel_id}/messages", data=message, **kwargs)

    def query_channels( self, guild_id, **kwargs):
        resp =  self._api_post( f"guilds/{ guild_id }/channels", method="GET" )
        log.info( resp )
        return [ objects.Channel( channel ) for channel in resp.json() ]

    def join_voice_channel( self, guild_id, channel: objects.Channel, **kwargs ):
        self._event_send( events.Update_Voice_State( data = events.Voice_State( guild_id=guild_id, channel=channel, **kwargs)._dict  ) )

    def leave_voice_channel( self, guild_id, **kwargs ):
         self._event_send( events.Update_Voice_State( data = events.Voice_State( guild_id=guild_id, channel=None, **kwargs)._dict  ) )

    def _api_post( self, subdivision, method="POST", **kwargs ): # add post to constants
        try:
            log.debug( f"Sending payload { kwargs['data'] } to {rest_url}{subdivision} as {method}" )
        except:
            log.debug( f"Requesting {rest_url}{subdivision} with {method}" )
        return requests.request( method,  f"{rest_url}{subdivision}", headers=header._header_gen(self.config.token), **kwargs )

    def _event_send( self, event: events.send_event ):  #one shot
        """
        Function to send event objects
        """
        return  self._websocket.send( event.pack() )

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
                self._voice_clients.append( VoiceClient( self, structs.Structure( voice_update ) ) )
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
        try:
            self._initialize( "wss://gateway.discord.gg" )
        except KeyboardInterrupt:
            log.info( "Quiting to <C-c>" )
            self.close()

    def close(self):
        self._websocket.close()

    def _initialize( self, url ):

        log.info("[green]Initializing IPC..." )

        self.heartbeat = queue.Queue(1)
        self._voice_clients = []
        self.session = {}


        with closing( websocket.create_connection( url ) ) as self._websocket:
            log.info( "[yellow]Initializing websocket" )

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
            log.debug(ready)
            del ready
            

            self._event_handler_d(heartbeat_interval)




    def _event_handler_d( self, heartbeat_interval ):
        hs = heartbeat_interval/1000
        while True:

            stat = time.time()
            jitter = random.random()
            jittered_hs = jitter * hs
            self._websocket.settimeout( hs )

            while True:

                try:
                    event_r =  json.loads( self._websocket.recv() ) 
                    event = events.recv_event( event_r )
                    now = time.time()
                    self._websocket.settimeout( jittered_hs - (now-stat) )

                except websocket.WebSocketTimeoutException:
                    # Do a heartbeat and restart the clock

                    log.debug("[yellow]Sending heartbeat")
                    heartbeat = events.Heartbeat()
                    log.info( "[yellow]Lub...?" )
                    self._websocket.send( heartbeat.pack() )

                    self._websocket.settimeout(5)
                    heartbeat_acknowledge = events.recv_event( json.loads(  self._websocket.recv() ) )
                    log.info( "[green]...Dub!" )

                    break

                match event.opcode:
                    case 0:
                        """
                        Dispatch
                        """
                        dispatch = events.Dispatch( **event_r )
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

                        pass
                    case _:
                        log.error("Unrecognised op code")
                        raise UnkownOpcode




class VoiceClient:
    def __init__( self, parent, voice_update ):
        self.parent = parent
        self._voice_update = voice_update
        log.info( "[yellow]Starting Voice Client..." )
        self.cmd = queue.Queue(30)
        self._initialize()

    def _initialize( self  ):
        log.info( "Voice sd" )

        self._voicesocket = websocket.create_connection( self._voice_update.voice_url + "?v=4" )
         # Voice socket cycle

        dispatch = events.Dispatch_v( json.loads(  self._voicesocket.recv() ) ) 

        assert dispatch.opcode == 8

        identify = events.Identify_v(
                events.config_identify_v( 
                    token=self._voice_update.voice_token,
                    server_id=self._voice_update.voice_guild_id,
                    user_id=self.parent.session.user.id,
                    session_id=self.parent.session.session_id ) 
                )

        log.debug( f"Sending => {identify.pack()}" )
        self._voicesocket.send( identify.pack() )

        ready = events.Ready_v( json.loads( self._voicesocket.recv()) )
        assert ready.opcode == 2

        self.info = ready.data

        log.debug( ready )

        self._event_handler_thread = threading.Thread( target=self._event_handler, args=( dispatch.data.heartbeat_interval ,) )
        self._event_handler_thread.start()


        log.info( "[green]Threads started, returning to parent..." )


    def _event_handler( self, heartbeat_interval ):
        hs = heartbeat_interval/1000
        while True:


            if not self.cmd.empty():
                self._cmd_handle()
            stat = time.time()
            jitter = random.random()
            jittered_hs = jitter * hs
            self._voicesocket.settimeout( hs )

            while True:

                try:
                    raw = self._voicesocket.recv()
                    if ( not raw ):
                        log.info( "Received None on voicesocket, returning..." )
                        return
                    log.info( f"Locals are { locals() }" )
                    event_r =  json.loads( raw ) 
                    event = events.recv_event( event_r )
                    now = time.time()
                    self._voicesocket.settimeout( jittered_hs - (now-stat) )

                except websocket.WebSocketTimeoutException:
                    # Do a heartbeat and restart the clock

                    log.debug("[yellow]Sending heartbeat")
                    heartbeat = events.Heartbeat_v()
                    log.info( "[purple]Lub...?" )
                    self._voicesocket.send( heartbeat.pack() )

                    self._voicesocket.settimeout(5)
                    heartbeat_acknowledge = events.recv_event( json.loads(  self._voicesocket.recv() ) )
                    assert heartbeat_acknowledge.opcode == 6
                    log.info( "[cyan]...Dub!" )

                    break

                match event.opcode:

                    case 11:
                        """
                        Heart beat acknowledged
                        """

                        pass
                    case _:
                        log.error("Unrecognised op code")
                        raise UnkownOpcode
    def _cmd_handle( self ):
        while not self.cmd.empty():
            (self.cmd.get_nowait())()


    def _set_speak( self, mic=True, soundshare=False, priority=False ):
        MIC = 1 << 0
        SOUNDSHARE = 1 << 1
        PRIORITY = 1 << 2
        speaking = 0
        if mic:
            speaking |= MIC
        if soundshare:
            speaking |= SOUNDSHARE
        if priority:
            speaking |= PRIORITY
        event =  events.Speaking( data=structs.Structure(speaking=speaking, delay=0, ssrc=self.info.ssrc) ) 
        log.info( event )
        self._voicesocket.send( event.pack() )

    def play( self, source ):
        vs = events.VoiceSelect( data= structs.Structure( protocol="udp", data=events.Select_v( address=self.info.ip, port=self.info.port )) ).pack() 
        log.info( vs )
        self._voicesocket.send( vs )
        session = structs.Structure( self._voicesocket.recv() )
        self._set_speak(mic=True, priority=True)
        self._playing_thread = threading.Thread( target=self._play, args=( source, session ) )
        self._playing_thread.start()

    def _play( self, source, session ):
        log.info( "Started new thread" )
        import nacl.secret
        import struct
        import socket
        sequence_int = 0
        send_time_ms = 0
        send_ssrc = os.urandom(4)
        soc = socket.socket()
        soc.connect( (self.info.ip, self.info.port) )

        while True: 
            # Grabbing the frames
            pcm = source.get_buffer()

            # Encoding them to opus
            opus_data = audio.encoder.encode( pcm ) # I think its importing the wrong pyogg
            log.debug( opus_data )

            # Encrypting
            key = bytes( session.data.secret_key )
            safe = nacl.secret.SecretBox( key )

            # Constructing header

            header = struct.pack( "!!!!!", 0x80, 0x78, sequence_int, send_time_ms, send_ssrc )
            nonce = header

            encrypted_data = safe.encrypt( opus_data, nonce )
            formed_data = header + encrypted_data

            log.info( formed_data )
            # send_to_be_encoded = stream.read( 1920 )
            sequence_int += 1
            send_time_ms += 20 # ms



    # def _voice_udp( self, ip, port, ssrc, voice_send_info, voice_recv_info ):

    #     while True:
    #         voice_socket =   udp.create_socket( remote_addr = ( ip, port ) )
    #         if voice_socket._protocol._is_ready:
    #             print ( voice_socket._protocol._is_ready )
    #             break
    #         else:
    #             print ( "[red bold]Connection refused... Re-trying in 5..." )
    #             time.sleep( 5 )
    #             continue

    #     discovery = bytes.fromhex( "00010046" ) + int.to_bytes( ssrc, 4, "big" ) + int.to_bytes( 0, 66, "big" )
    #     voice_socket.sendto(discovery) 

    #     data, addr =  voice_socket.recvfrom()
    #     recv_ip = "".join([ chr( i )  for i in data[8:50] if i !=b'0x00' ])
    #     recv_port = int.from_bytes( data[-2:] , "big" )

    #     repl = dict()
    #     repl["op"] = 1
    #     repl["d"] = dict()
    #     repl["d"]["protocol"] = "udp"
    #     repl["d"]["data"] = dict()
    #     repl["d"]["data"]["address"] = recv_ip
    #     repl["d"]["data"]["port"] = recv_port
    #     repl["d"]["data"]["mode"] = "xsalsa20_poly1305"


    #     voice_send_info.put( json.dumps( repl ) )

    #     data, addr =  voice_socket.recvfrom()

    #     repl =  voice_recv_info.get()
    #     # ssrc = repl["d"]["ssrc"]
    #     key =  bytes( repl["d"]["secret_key"] ) 
    #     print (len(key))
    #     safe = secret.SecretBox( key )

    #     decoder = opus.decoder.Decoder( 48000, 2 )
    #     encoder = opus.encoder.Encoder( 48000, 2, 2049 )
    #     send_sequence = 0
    #     sequence = 0
    #     send_ssrc = os.urandom(4)
    #     send_time = 0
    #     voice_send_info.put( json.dumps ({ "op" : 5, "d" : { "speaking": 5, "delay" : 0, "ssrc" : int.from_bytes( send_ssrc ) } } ) ) 
    #     f = open( "test.raw", "wb" )

    #     with Live( "recieving" ) as live:
    #         while True:

    #             try:
    #                 data, addr =  voice_socket.recvfrom()
    #             except Exception as e:
    #                 inspect( e )
    #             print( sequence )
    #             print ( "." )
    #             td = ""

    #             if data[0] == 129:
    #                 td += ("[red bold]Silence\n") 
    #                 live.update(td)
    #                 continue
    #             elif data[0] == 128:

    #                 td += ( "[green bold]Voice\n")

    #                 sequence = data[2:4]
    #                 time_stamp = data[4:8]

    #                 nonce = bytearray(24)
    #                 nonce[:12] = data[:12] # Setting nonce from header
    #                 encrypted_data = data[12:]

    #                 decrypted_data = safe.decrypt( bytes( encrypted_data ), bytes( nonce ) ) 

    #                 decoded_data = decoder.decode( decrypted_data, 960 )
    #                 print( decoded_data )
    #                 f.write( decoded_data )

    #             print( len ( send_to_be_encoded ) )
    #             if len( send_to_be_encoded ):
    #                 send_data = send_header + safe.encrypt( encoder.encode( send_to_be_encoded, 960 ), bytes( send_nonce ) ) 
    #             else:
    #                 print ( "Over" )



    #             voice_socket.sendto( send_data )
    #             send_sequence += 1
    #             send_time += 20
    #             td += f"[purple]Length: [cyan]\n[/cyan purple]"
    #             live.update(td)


    #     voice_socket.close()

