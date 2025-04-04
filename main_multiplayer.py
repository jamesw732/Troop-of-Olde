from ursina import *

from source.networking import network
from source.networking.connect import *
from source.networking.disconnect import *
from source.networking.register import *


app = Ursina(borderless=False)
app.run()