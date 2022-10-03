import json
from rich import print
from rich import pretty
from rich import inspect
pretty.install()


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
    def  pack( self ):
        return json.dumps( self._dict )

class gateway_message( base_struct ):
    _lookup = {
            "opcode" : "op",
            "data" : "d"
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
    def __init__( self, token, properties, intents, **kwargs ):
        super().__init__( **kwargs )
        self.token = token
        self.properties = properties._dict
        self.intents = intents


class Heartbeat( gateway_message ):
    """
    A heartbeat struct, generally, no arguments, can set opcode( not reommended ) and data ( not recommended but harmless )
    Could result in error 4002, could not parse, from server
    """
    _defaults = {
            "opcode" : 1,
            "data" : None
            }

class Identify( gateway_message ):
    """
    An identify struct, takes one argument, config, of type, config_identify, which configures token, properties, compression, presence and intents

    token and presence are safe to touch, remainning, change at your own risk
    """

    _defaults = {
            "opcode" : 2
            }

    def __init__( self, config, **kwargs ):
        super().__init__( **kwargs )
        self.data = config._dict


## Tests

if __name__ == "__main__":
    
    print( "Testing gateway message" )
    gm = gateway_message( opcode=10, data = gateway_message( opcode=9 ).pack() )
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

