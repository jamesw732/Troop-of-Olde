from ursina import *
from player import *

app = Ursina()

Sky(texture="sky_sunset.jpg")
ground = Entity(model="plane", texture="grass", scale=50, collider="box")

player = Player(ground, model='cube', color=color.orange, scale_y=2, collider="box", origin=(0, -0.5, 0), position=(0, 0.05, 0))
obstacle = Entity(model="cube", color=color.red, collider="box", scale=5, origin=(0, -0.5, 0), position=(10, 0, 10))
roof = Entity(model="cube", color=color.green, collider="box", origin=(0, 0, 0), position=(-10, 4, -10), scale_x=5, scale_z=5)
ramp = Entity(model="plane", color=color.black, scale=15, collider="box", position=(10, 3.24, -10), rotation=(80, 0, 0))
lopsided= Entity(model="cube", color=color.blue, collider="box", scale=5, origin=(0, 0, 0), position=(-10, 0, 10), rotation=(45, 0, 0))
basement = Entity(model="plane", texture="brick", scale_x=200, scale_z=200, collider="box", position = (0, -100, 0))

def input(key):
    if key == "escape":
        player.move_to((0, 5, 0))
        player.grav = 0

app.run()