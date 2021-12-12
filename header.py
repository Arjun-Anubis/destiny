#All glob variables

from rich import print
from rich import pretty
pretty.install()

IDENTIFY=2
VOICE_CONNECT=4

with open( "token" ) as f:
    token = f.read()[:-1] #Removing newline
