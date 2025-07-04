from ursina import *

from source.client.input_handler import InputHandler
from source.networking import network
from source.networking.connect import *
from source.networking.disconnect import *
from source.networking.register import *


app = Ursina(borderless=False)
input_handler = InputHandler()
app.run()