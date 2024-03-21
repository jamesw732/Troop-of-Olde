from ursina import *
import numpy


class Player(Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.speed = 50
        self.camdistance = 20
        self.height = self.scale_y

        self.focus = Entity(model="cube", visible=False, position=self.position + Vec3(0, 0.8 * self.height, 0))
        camera.parent = self.focus
        camera.position = (0, 0, -1 * self.camdistance)

        self.max_jump_height = 3
        self.cur_jump_height = 0
        self.time_of_jump = 0.2
        self.jumping = False

        self.grounded = True
        # self.ground_detection = boxcast()

        self.traverse_target = scene
        self.ignore_list = [self]

    def update(self):
        self.move_keyboard()
        self.rotate_camera()
        self.jump()
        self.grounded_check()
        self.gravity()

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
        if key == "space":
            self.start_jump()
        # if key == "space up" and self.cur_jump_height: # track cur jump time for this, after may not be used correctly
        #     after(self.time_of_jump / 2 - self.cur_jump_time, self.cancel_jump())

    def grounded_check(self):
        self.grounded = self.intersects()

    def gravity(self):
        if not self.grounded and not self.jumping:
            grav = -10 * time.dt
            self.move((0, grav, 0))

    def jump(self):
        if self.jumping:
            dist = time.dt * self.max_jump_height / self.time_of_jump
            if self.cur_jump_height + dist >= self.max_jump_height:
                dist = self.max_jump_height - self.cur_jump_height
            self.move((0, dist, 0))
            self.cur_jump_height += dist
            if self.cur_jump_height >= self.max_jump_height:
                self.cancel_jump()

    def start_jump(self):
        if self.grounded:
            self.jumping = True

    def cancel_jump(self):
        self.jumping = False
        self.cur_jump_height = 0

    def move_keyboard(self):
        """Handle keyboard inputs for movement"""
        movement_inputs = Vec3(held_keys['e'] - held_keys['q'], 0, held_keys['w'] - held_keys['s']).normalized()
        theta = numpy.radians(-1 * self.rotation_y)
        rotation_matrix = numpy.array([[numpy.cos(theta), -1 * numpy.sin(theta)], [numpy.sin(theta), numpy.cos(theta)]])
        move_direction = rotation_matrix @ numpy.array([movement_inputs[0], movement_inputs[2]])
        movement_delta = Vec3(move_direction[0], 0, move_direction[1]) * time.dt * self.speed

        self.move(movement_delta)

    def rotate_camera(self):
        """Handle keyboard/mouse inputs for camera"""
        # Keyboard Rotation:
        updown_rotation = held_keys["up arrow"] - held_keys["down arrow"]
        leftright_rotation = held_keys['d'] - held_keys['a']
        self.focus.rotate((0, leftright_rotation * numpy.cos(numpy.radians(self.focus.rotation_x)), 0))
        self.focus.rotate((updown_rotation, 0, 0))

        max_vert_rotation = 80

        # Mouse rotation:
        if held_keys["right mouse"]:
            diff = mouse.position - self.mouselock
            vel = Vec3(-1 * diff[1], diff[0] * numpy.cos(numpy.radians(self.focus.rotation_x)), 0)
            self.focus.rotate(vel * 100)
            mouse.position = self.mouselock

        # Adjust everything
        self.focus.rotation_z = 0
        self.rotation_y = self.focus.rotation_y
        if self.focus.rotation_x > max_vert_rotation:
            self.focus.rotation_x = max_vert_rotation
        if self.focus.rotation < -max_vert_rotation:
            self.focus.rotation_x = -max_vert_rotation

    def move(self, delta):
        """Move both player and focus"""
        self.position += delta
        self.focus.position = self.position