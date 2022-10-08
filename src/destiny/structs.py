import json
from destiny.header import *
from destiny.exceptions import *



from collections.abc import MutableMapping


class structure_e(MutableMapping):
    """A dictionary that applies an arbitrary key-altering
       function before accessing the keys"""

    def __init__(self, *args, **kwargs):
        self._dict = dict()
        self.update(dict(*args, **kwargs))  # use the free update to set keys
        

    def __getitem__(self, key):
        # return self._dict[self._keytransform(key)]
        try:
            return self._dict[key]
        except KeyError:
            raise notFound

    def __setitem__(self, key, value, core=False):
        self._dict[self._keytransform(key)] = value

    def __delitem__(self, key):
        del self._dict[self._keytransform(key)]

    def __iter__(self):
        return iter(self._dict)

    def __len__(self):
        return len(self._dict)

    def _keytransform(self, key):
        return self._lookup[key]

    __getattr__ = __getitem__


class Result:
    def __init__( self, result: bool ):
        self.result = result
    def __bool__( self ):
        return bool( self.result )

class structure(structure_e):
    _defaults = {}

    def __init__( self, **kwargs ):
        super().__setattr__( "_dict", dict() )
        # self._dict = dict()
        self.update(self._defaults)
        self.update(dict(**kwargs))

    def __str__( self ):
        return f"<{self.__class__.__name__}>\n{self._dict}"
    def __repr__( self ):
        return f"<{self.__class__.__name__}>\n{self._dict}"



class implimented_structure( structure ):
    def  pack( self ) -> str:
        return json.dumps( self._dict )
    def __setattr__( self, name, value ):
        self._dict.update( {self._lookup[name]: value} )
        self.update()
    # def update( self ):
    #     super().__setattr__( "_json", json.dumps( self.pack() ) )


class unimplimented_structure( structure ): 
    """
    Immuatble Wrapper json
    """
    def __init__( self, data: dict(), **kwargs ):
        self._pre_init()
        self._dict = data 
        for key in self._dict:
            if  type( self._dict[key] ) == type( dict() ):
                self._dict[key] = unimplimented_structure( self._dict[key] ) # recursive
        self._post_init()


class Channel( unimplimented_structure ):
    def __str__( self ):
        return self.name
    def __repr__( self ):
        return self.name

class Guild( unimplimented_structure ):
    def __str__( self ):
        return self.name
    def __repr__( self ):
        return self.name



class event( implimented_structure ):
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

class Dispatch_v( Dispatch ):
    pass

class Message( recv_event ):
    _lookup = {
            "id" : "id", #string
            "channel_id": "channel_id", #string
            "author": "author", #object _author_
            "content" : "content", #string
            "timestamp" : "time",
            "edited_timestamp" : "edited_time",
            "tts" : "tts", #bool
            "mention_everyone" : "mention_everyone",
            "mentions" : "mentions",
            "mention_roles" :"mention_roles",
            "mention_channels" : "mention_channels",
            "attachments" : "attachments", #list object
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


class network_properties( implimented_structure ):
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

class config_identify( implimented_structure ):
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

class Update_Voice_State( send_event ):
    _defaults = {
            "opcode" : 4,

            }
class Voice_State( implimented_structure ):
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
    def __init__( self, guild_id, channel: Channel, **kwargs ):
        super().__init__( **kwargs )
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

