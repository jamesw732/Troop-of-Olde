from ursina import *
from player import *
from npc import *
from combat import *
from world_gen import *

app = Ursina(borderless=False)
world = GenerateWorld("zones/demo.json")