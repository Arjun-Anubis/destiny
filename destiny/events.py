from __future__ import annotations
from destiny.header import *
from destiny.exceptions import *
import destiny.structs as structs
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import destiny.objects as objects

import json
import jsons
import uuid

class event( structs.implimented_structure ):
    pass

class send_event( event ):
    _lookup = {
            "opcode" : "op",
            "data" : "d"
            }
class recv_event( event ):
    _lookup = {
            "op" : "opcode",
            "t" : "type",
            "s" : "serial",
            "d" : "data"
            }


class Dispatch( recv_event ):
    pass

class Dispatch_v( Dispatch ):
    pass


class network_properties( structs.implimented_structure ):
    _lookup = {
            "os" : "os",
            "lib": "browser",
            "dev": "device"
            }
    _defaults = {
            "os" : "linux",
            "lib" : "destiny",
            "dev" : "destiny"
            }

class config_identify( structs.implimented_structure ):
    _lookup = {
            "token" : "token",
            "properties" : "properties",
            "comp" : "compress",
            "presence": "presence",
            "intents": "intents",
            "threshhold": "large_threshold"
            }
    _defaults = {
            "comp": False,
            "threshhold" : 50
            }
    def __init__( self, token: str, properties: network_properties, intents: int, **kwargs ):
        super().__init__( **kwargs )
        self.token = token
        self.properties = properties._dict
        self.intents = intents

class config_identify_v( structs.implimented_structure ):
    _lookup = {
            "token" : "token",
            "server_id" : "server_id",
            "user_id" : "user_id",
            "session_id" : "session_id"
            }

    _defaults = { }

    def __init__( self, token: str, server_id: str, user_id: str, session_id: str, **kwargs ):
        super().__init__( **kwargs )
        self.token = token
        self.server_id = server_id
        self.user_id = user_id
        self.session_id = session_id

class Heartbeat( send_event ):
    """
    A heartbeat struct, generally, no arguments, can set opcode( not reommended ) and data ( not recommended but harmless )
    Could result in error 4002, could not parse, from server
    """
    _defaults = {
            "opcode" : 1,
            "data" : None
            }

class Heartbeat_v( send_event ):
    """
    A heartbeat struct, generally, no arguments, can set opcode( not reommended ) and data ( not recommended but harmless )
    Could result in error 4002, could not parse, from server
    """
    _defaults = {
            "opcode" : 3,
            "data" : uuid.uuid4().int
            }

class Hello( recv_event ):
    pass
class Ready( recv_event ):
    pass
class Ready_v( recv_event ):
    pass
class Update_Voice_State( send_event ):
    _defaults = {
            "opcode" : 4,

            }
class Voice_State( structs.implimented_structure ):
    """
    A update voice state struct, has a few arguments to initalize values channel_id, guild_id, self_mute, self_deaf
    """
    _lookup = {
            "channel_id" : "channel_id",
            "self_mute" : "self_mute",
            "guild_id" : "guild_id",
            "self_deaf" : "self_deaf"
            }

    _defaults = {
            "channel_id" : None, # leave by default
            "self_mute" : False,
            "self_deaf" : False
            }
    def __init__( self, guild_id, channel: objects.Channel, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        self.guild_id = guild_id
        if channel:
            self.channel_id = channel.id
        else:
            self.channel_id = channel

class Identify( send_event ):
    """
    An identify struct, takes one argument, config, of type, config_identify, which configures token, properties, compression, presence and intents

    token and presence are safe to touch, remainning, change at your own risk
    """

    _defaults = {
            "opcode" : 2
            }

    def __init__( self, config: config_identify, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        self.data = config._dict

# Add remaining gateway codes Resume, request guild members, update voice state, update presence

class Identify_v( send_event ):
    """
    An identify struct, takes one argument, config, of type, config_identify, which configures token, properties, compression, presence and intents

    token and presence are safe to touch, remainning, change at your own risk
    """

    _defaults = {
            "opcode" : 0
            }

    def __init__( self, config: config_identify_v, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        self.data = config._dict

# Add remaining gateway codes Resume, request guild members, update voice state, update presence

