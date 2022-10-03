#All glob variables

TOKEN_FILE = "../assets/token"

from rich import print
from rich import pretty
from rich import inspect
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.traceback import install


import logging

pretty.install()
install()

from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    level="INFO", format=FORMAT, datefmt="[%X]", handlers=[RichHandler(markup=True)]
)

log = logging.getLogger("rich")

rest_url = "https://discordapp.com/api/"

VOICE_CONNECT=4

with open( TOKEN_FILE ) as f:
    token = f.read()[:-1] #Removing newline

HEADERS = { "Authorization" : f"Bot {token}", "User-Agent" : "DiscordBot (https://github.com/Arjun-Anubis/snowflake, v0.1)" }
DEST_DIR = "../assets/hw"
