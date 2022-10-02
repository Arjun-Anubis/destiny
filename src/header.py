#All glob variables

TOKEN_FILE = "../assets/token"

from rich import print
from rich import pretty
pretty.install()

IDENTIFY=2
VOICE_CONNECT=4

with open( TOKEN_FILE ) as f:
    token = f.read()[:-1] #Removing newline
