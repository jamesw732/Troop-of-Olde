from ursina import *

from source.client.input_handler import InputHandler
from source.client.connect import *
from source.client.world_responses import *
from source.network import network


app = Ursina(borderless=False)
input_handler = InputHandler()
app.run()