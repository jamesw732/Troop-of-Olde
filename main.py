from ursina import *
import math
# create a window
app = Ursina()

class Player(Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.speed = 5
        self.camdistance = 100
        self.focus = Entity(model="cube", scale=0.1, position=self.position + Vec3(0, 0.8 * self.scale_y, 0))
        camera.parent = self.focus
        camera.position = (0, 0, -1 * self.camdistance)

    def update(self):
        movement_delta = Vec3(held_keys['e'] - held_keys['q'], 0, held_keys['w'] - held_keys['s']).normalized()
        movement_delta *= time.dt * 5
        self.position += movement_delta
        self.focus.position += movement_delta
        updown_rotation = held_keys["up arrow"] - held_keys["down arrow"]
        leftright_rotation = held_keys['d'] - held_keys['a']
        self.focus.rotate((0, leftright_rotation * math.cos(math.radians(self.focus.rotation_x)), 0))
        if abs(self.focus.rotation_x + updown_rotation) < 89:
            self.focus.rotate((updown_rotation, 0, 0))
        self.focus.rotation_z = 0
        self.rotation_y = self.focus.rotation_y
        camera.position = (0, 0, -1 * self.camdistance)

    def input(self, key):
        if key == "scroll up":
            self.camdistance += 10
        if key == "scroll down":
            self.camdistance -= 10

player = Player(model='cube', color=color.orange, scale_y=2, collider="box", origin=(0, -.5, 0))
ground = Entity(model = "plane", texture="grass", scale = 200, collider="box")

Sky()
app.run()