import json
from destiny.header import *


class base_struct:
    _defaults = {}

    def __init__( self, **kwargs ):
        super().__setattr__( "_dict", dict() )
        for key in self._defaults:
            self.__setattr__( key, self._defaults[key] )
        for key in kwargs:
            self.__setattr__( key, kwargs[key] )
        super().__setattr__( "_json", json.dumps( self.pack() ) )

    def __setattr__( self, name, value ):
        self._dict.update( {self._lookup[name]: value} )
        self.update()
    def update( self ):
        super().__setattr__( "_json", json.dumps( self.pack() ) )
    def  pack( self ) -> str:
        return json.dumps( self._dict )

class event( base_struct ):
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
    # __get_lookup = {
    #         "opcode" : "op",
    #         "data" : "d",
    #         "serial" : "s",
    #         "type" : "t"
            # }
    def __getattr__( self, attr ):        
        return self._dict[ attr ]
    def __getitem__( self, attr ):
        return self._dict[ attr ]

class User( recv_event ):
    _lookup = {
            "id" : "id",
            "username" : "username",
            "discriminator" : "discriminator",
            "avatar" : "avatar",
            "bot" : "is_bot",
            "system" : "is_system",
            "mfa_enabled" : "is_mfa_enabled",
            "banner" : "banner",
            "accent_color" :"accent_color",
            "locale" : "locale",
            "verified" : "is_verified",
            "email" : "email",
            "flags": "flags",
            "premium_type" : "premium_type",
            "public_flags" : "public_flags",


            "avatar_decoration" : "avatar_decoration"
            }

class Dispatch( recv_event ):
    pass

class Message( recv_event ):
    _lookup = {
            "id" : "id",
            "channel_id": "channel_id",
            "author": "author",
            "content" : "content",
            "timestamp" : "time",
            "edited_timestamp" : "edited_time",
            "tts" : "tts",
            "mention_everyone" : "mention_everyone",
            "mentions" : "mentions",
            "mention_roles" :"mention_roles",
            "mention_channels" : "mention_channels",
            "attachments" : "attachments",
            "embeds" : "embeds",
            "reactions" : "reactions",
            "nonce" : "nonce",
            "pinned" : "pinned",
            "webhook_id" : "webhook_id",
            "type" : "type",
            "activity" : "activity",
            "application": "app",
            "application_id" : "app_id",
            "message_reference" : "message_reference",
            "flags" : "flags",
            "referenced_message": "referenced_message",
            "interaction" : "interaction",
            "thread" : "thread",
            "components" : "components",
            "sticker_items" : "sticker_items",
            "stickers" : "stickers",
            "position" : "position",


            "guild_id" : "guild_id",
            "member" : "member",
            }


class network_properties( base_struct ):
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

class config_identify( base_struct ):
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


class Heartbeat( send_event ):
    """
    A heartbeat struct, generally, no arguments, can set opcode( not reommended ) and data ( not recommended but harmless )
    Could result in error 4002, could not parse, from server
    """
    _defaults = {
            "opcode" : 1,
            "data" : None
            }

class Identify( send_event ):
    """
    An identify struct, takes one argument, config, of type, config_identify, which configures token, properties, compression, presence and intents

    token and presence are safe to touch, remainning, change at your own risk
    """

    _defaults = {
            "opcode" : 2
            }

    def __init__( self, config: config_identify, **kwargs ):
        super().__init__( **kwargs )
        self.data = config._dict

# Add remaining gateway codes Resume, request guild members, update voice state, update presence



## Tests

if __name__ == "__main__":
    
    print( "Testing gateway message" )
    gm = send_event( opcode=10, data = gateway_message( opcode=9 ).pack() )
    inspect( gm, private=True )
    del gm


    print( "Sample heartbeat" )
    heartbeat = Heartbeat( )
    inspect( heartbeat, private=True)
    del heartbeat

    print( "Heartbeat, modified" )
    heartbeat_mod = Heartbeat( opcode=27, data=76 )
    inspect( heartbeat_mod, private=True)
    del heartbeat_mod

    print( "id config default" )
    config = config_identify( token="sample", properties={}, intents=512)
    inspect( config, private=True)
    print( "Identify" )
    Id = Identify( config )
    inspect( Id, private=True )
    print( Id._json )

