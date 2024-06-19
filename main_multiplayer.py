from ursina import *

from source.character import *
from source.networking.base import *
from source.networking.continuous import *
from source.networking.login import *
from source.networking.logout import *
from source.world_gen import *


app = Ursina(borderless=False)
app.run()