from ursina import *
import numpy


class Player(Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.speed = 30
        self.camdistance = 20
        self.height = self.scale_y

        self.focus = Entity(model="cube", visible=False, position=self.position + Vec3(0, 0.8 * self.height, 0), rotation=(1, 0, 0))
        camera.parent = self.focus
        camera.position = (0, 0, -1 * self.camdistance)

        self.max_jump_height = self.height * 1.5
        self.rem_jump_height = self.max_jump_height
        self.max_jump_time = 0.3
        self.rem_jump_time = self.max_jump_time
        self.jumping = False
        self.grounded_direction = Vec3(0, 0, 0)
        self.jumping_direction = Vec3(0, 0, 0)

        self.grounded = True
        self.grav = 0

        self.traverse_target = scene
        self.ignore_traverse = [self]


    def update(self):
        # Put all inputs together into one velocity vector
        move = self.move_keyboard()
        grav = self.gravity()
        jump = self.jump()
        velocity = move + grav + jump
        self.move(velocity * time.dt)

        self.rotate_camera()
        self.grounded_check()

        camera.position = (0, 0, -1 * self.camdistance)
        # Uncomment this to see what a key is called in Ursina
        # print(held_keys)

    def input(self, key):
        if key == "scroll down":
            self.camdistance = min(self.camdistance + 1, 150)
        if key == "scroll up":
            self.camdistance = max(self.camdistance - 1, 0)
        if key == "right mouse down":
            mouse.visible = False
            self.mouselock = mouse.position
        if key == "right mouse up":
            mouse.visible = True
        if key == "space":
            self.start_jump()

    def grounded_check(self):
        self.grounded = self.intersects()

    def gravity(self):
        if not self.grounded and not self.jumping:
            self.grav -= 1
        elif self.grounded:
            self.grav = 0
        return Vec3(0, self.grav, 0)

    def jump(self):
        if self.jumping:
            speed = self.max_jump_height / self.max_jump_time
            if self.rem_jump_height - speed * time.dt <= 0:
                speed = self.rem_jump_height / self.max_jump_time
                self.cancel_jump()
                return Vec3(0, speed, 0)
            else:
                self.rem_jump_height -= speed * time.dt
                return Vec3(0, speed, 0)
        return Vec3(0, 0, 0)

    def start_jump(self):
        if self.grounded:
            self.jumping = True

    def cancel_jump(self):
        self.jumping = False
        self.rem_jump_height = self.max_jump_height

    def move_keyboard(self):
        """Handle keyboard inputs for movement"""
        movement_inputs = Vec3(held_keys['e'] - held_keys['q'], 0, held_keys['w'] - held_keys['s']).normalized()
        theta = numpy.radians(-1 * self.rotation_y)
        rotation_matrix = numpy.array([[numpy.cos(theta), -1 * numpy.sin(theta)], [numpy.sin(theta), numpy.cos(theta)]])
        move_direction = rotation_matrix @ numpy.array([movement_inputs[0], movement_inputs[2]])
        move_direction = Vec3(move_direction[0], 0, move_direction[1])
        if self.grounded:
            self.grounded_direction = move_direction
        else:
            move_direction = 0.8 * self.grounded_direction + 0.2 * move_direction
        return move_direction * self.speed

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

    def move_to(self, loc):
        self.position = loc
        self.focus.position = loc