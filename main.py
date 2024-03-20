from ursina import *
from player import *

app = Ursina()

Sky(texture="sky_sunset.jpg")

player = Player(model='cube', color=color.orange, scale_y=2, collider="box", origin=(0, -.5, 0))
ground = Entity(model = "plane", texture="grass", scale = 50, collider="box")

app.run()