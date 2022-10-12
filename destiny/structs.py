from destiny.header import *
from destiny.exceptions import *

import json
import jsons
import uuid


from collections.abc import MutableMapping


class Structure(MutableMapping):
    """A dictionary that applies an arbitrary key-altering
       function before accessing the keys"""

    _lookup = {}
    def __init__(self, *args, **kwargs):
        self._dict = dict()
        self.update(dict(*args, **kwargs))  # use the free update to set keys
        

    def __getitem__(self, key):
        # return self._dict[self._keytransform(key)]
        try:
            return self._dict[key]
        except KeyError:
            raise notFound

    def __setitem__(self, key, value ):
        if type(value) == dict:
            self._dict[key] = Structure(value)
        else:
            self._dict[key] = value

    def __delitem__(self, key):
        del self._dict[key]

    def __iter__(self):
        return iter(self._dict)

    def __len__(self):
        return len(self._dict)

    def __str__( self ):
        return f"{self._dict}"

    __getattr__ = __getitem__
    __repr__ = __str__


class Result:
    def __init__( self, result: bool ):
        self.result = result
    def __bool__( self ):
        return bool( self.result )

class ImmutableStructure(Structure):
    """
    Structure types, which have predefined fields and lookup tables, as well as defaults
    """
    _defaults = {}

    def __init__( self, *args, **kwargs ):
        super().__setattr__( "_dict", dict() )
        #Has defaults
        self.update(self._defaults)
        self.update(dict(*args, **kwargs))

    def __str__( self ):
        return f"{self.__class__.__name__}({self._dict})"

    __repr__ = __str__

    def _keytransform(self, key):
        return self._lookup[key]

    def __delitem__(self, key):
        del self._dict[self._keytransform(key)]

    def __setitem__(self, key, value, core=False):
        if type(value) == dict:
            self._dict[self._keytransform(key)] = Structure(value)
        else:
            self._dict[self._keytransform(key)] = value


class implimented_structure( ImmutableStructure ):
    def  pack( self ) -> str:
        return json.dumps( jsons.dump( self ) )

    def __setattr__( self, name, value ):
        self._dict.update( {self._lookup[name]: value} )
        self.update()

    # def update( self ):
    #     super().__setattr__( "_json", json.dumps( self.pack() ) )


class unimplimented_structure( Structure ): 
    pass




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

