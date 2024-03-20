from ursina import *
import numpy


class Player(Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.speed = 50
        self.camdistance = 20
        self.focus = Entity(model="cube", visible=False, position=self.position + Vec3(0, 0.8 * self.scale_y, 0))
        camera.parent = self.focus
        camera.position = (0, 0, -1 * self.camdistance)

    def update(self):
        self.move()
        self.rotate_camera()
        # Uncomment this to see what a key is called in Ursina
        # print(held_keys)

    def input(self, key):
        if key == "scroll down":
            self.camdistance = min(self.camdistance + 1, 100)
        if key == "scroll up":
            self.camdistance = max(self.camdistance - 1, 0)
        if key == "right mouse down":
            mouse.visible = False
            self.mouselock = mouse.position
        if key == "right mouse up":
            mouse.visible = True

    def move(self):
        movement_inputs = Vec3(held_keys['e'] - held_keys['q'], 0, held_keys['w'] - held_keys['s']).normalized()
        theta = numpy.radians(-1 * self.rotation_y)
        rotation_matrix = numpy.array([[numpy.cos(theta), -1 * numpy.sin(theta)], [numpy.sin(theta), numpy.cos(theta)]])
        move_direction = rotation_matrix @ numpy.array([movement_inputs[0], movement_inputs[2]])
        movement_delta = Vec3(move_direction[0], 0, move_direction[1]) * time.dt * self.speed

        self.position += movement_delta
        self.focus.position += movement_delta

    def rotate_camera(self):
        # Keyboard Rotation:
        updown_rotation = held_keys["up arrow"] - held_keys["down arrow"]
        leftright_rotation = held_keys['d'] - held_keys['a']
        self.focus.rotate((0, leftright_rotation * numpy.cos(numpy.radians(self.focus.rotation_x)), 0))
        if abs(self.focus.rotation_x + updown_rotation) < 89:
            self.focus.rotate((updown_rotation, 0, 0))

        # Mouse rotation:
        if held_keys["right mouse"]:
            # vel = Vec3(-1 * mouse.velocity[1], mouse.velocity[0], 0)
            diff = mouse.position - self.mouselock
            vel = Vec3(-1 * diff[1], diff[0], 0)
            self.focus.rotate(vel * 100)
            mouse.position = self.mouselock

        # Adjust everything
        self.focus.rotation_z = 0
        self.rotation_y = self.focus.rotation_y
        camera.position = (0, 0, -1 * self.camdistance)