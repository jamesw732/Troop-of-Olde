from ursina import *

from source.character import *
from source.networking import *
from source.networking.continuous import *
from source.networking.connect import *
from source.networking.disconnect import *
from source.world_gen import *


app = Ursina(borderless=False)
app.run()