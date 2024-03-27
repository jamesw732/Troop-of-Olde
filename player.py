from ursina import *
import numpy


class Player(Entity):
    def __init__(self, *args, speed=30, camdistance=20, **kwargs):
        """Initialize entity, instantiate some instance variables."""
        super().__init__(*args, **kwargs)
        self.speed = speed
        self.camdistance = camdistance
        self.height = self.scale_y

        self.focus = Entity(model="cube", visible=False, position=self.position + Vec3(0, 0.5 * self.height, 0), rotation=(1, 0, 0))
        camera.parent = self.focus
        camera.position = (0, 0, -1 * self.camdistance)

        self.max_jump_height = self.height * 1.5
        self.rem_jump_height = self.max_jump_height
        self.max_jump_time = 0.3
        self.rem_jump_time = self.max_jump_time
        self.jumping = False
        self.grounded_direction = Vec3(0, 0, 0)
        self.jumping_direction = Vec3(0, 0, 0)

        self.grounded = False
        self.grav = 0

        self.traverse_target = scene
        self.ignore_traverse = [self]

    def update(self):
        """Handle things that happen every frame"""
        # Put all inputs together into one velocity vector
        move = self.move_keyboard()
        grav = self.gravity()
        jump = self.jump()
        self.velocity = move + grav + jump
        self.handle_grounding()
        self.handle_collision()
        self.handle_upward_collision()
        self.move()

        self.rotate_camera()
        self.adjust_camera_zoom()

        self.move_focus()
        # Uncomment this to see what a key is called in Ursina
        # print(held_keys)

    def input(self, key):
        """Handle things that happen once upon an input"""
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

    def handle_grounding(self):
        """Handles logic for whether the character is grounded or not.
        Doesn't move the player at all, just handles logic for whether or not the player is grounded"""
        if self.velocity[1] > 0:
            self.grounded = False
        elif self.velocity[1] == 0:
            ground = raycast(self.position, direction=(0, -1, 0), distance=0.1, ignore=self.ignore_traverse)
            self.grounded = ground.hit
        else:
            ground = raycast(self.position, direction=(0, -1, 0), distance=abs(self.velocity[1] * time.dt), ignore=self.ignore_traverse)
            if ground.hit:
                self.grounded = True

    def handle_collision(self):
        """Handles most of the collision logic."""
        norm = distance((0, 0, 0), self.velocity) * time.dt
        pos = self.position
        # Sometimes misses entity. Could be due to player clipping through beforehand, could be due to a raycast bug. Likely the former.
        collision_check = raycast(pos, direction=self.velocity, distance=norm, ignore=self.ignore_traverse)
        if collision_check.hit:
            normal = collision_check.world_normal
            if numpy.dot(normal, self.velocity) < 0:
                self.velocity = self.velocity - (numpy.dot(normal, self.velocity)) * normal
                # Check if new velocity passes through any entities, ie concave case
                norm2 = distance((0, 0, 0), self.velocity) * time.dt
                ray = raycast(pos, direction=self.velocity, distance=norm2, ignore=self.ignore_traverse)
                if ray.hit:
                    self.velocity = Vec3(0, 0, 0)

    def handle_upward_collision(self):
        """Blocks upward movement when jumping into a ceiling"""
        if self.velocity[1] < 0:
            return
        pos = self.position + Vec3(0, self.height, 0)
        ceiling = raycast(pos, direction=(0, 1, 0), distance=self.velocity[1] * time.dt, ignore=self.ignore_traverse)
        if ceiling.hit:
            self.velocity[1] = 0
            self.move_to(ceiling.world_point - Vec3(0, self.height, 0))

    def gravity(self):
        """If not grounded and not jumping, subtract y (linear in time) from velocity vector"""
        if not self.grounded and not self.jumping:
            self.grav -= 1
        elif self.grounded:
            self.grav = 0
        return Vec3(0, self.grav, 0)

    def jump(self):
        """If jumping, add some y to velocity vector"""
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
        """Set self.jumping"""
        if self.grounded:
            self.jumping = True

    def cancel_jump(self):
        """Reset self.jumping, remaining jump height"""
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
        # elif self.jumping:
        #     self.grounded_direction = self.move_direction = (0.5 * self.grounded_direction + 0.5 * move_direction).normalized()
        else:
            move_direction = (0.8 * self.grounded_direction + 0.2 * move_direction).normalized()
        return move_direction * self.speed

    def rotate_camera(self):
        """Handle keyboard/mouse inputs for camera"""
        # Keyboard Rotation:
        updown_rotation = held_keys["up arrow"] - held_keys["down arrow"]
        leftright_rotation = held_keys['d'] - held_keys['a']
        # Slow down left/right rotation by multiplying by cos(x rotation)
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

    def adjust_camera_zoom(self):
        """Set camera zoom. Handles camera collision with entities"""
        theta = numpy.radians(90 - self.focus.rotation_x)
        phi = numpy.radians(-self.focus.rotation_y)
        direction = Vec3(numpy.sin(theta) * numpy.sin(phi), numpy.cos(theta), -1 * numpy.sin(theta) * numpy.cos(phi))
        ray = raycast(self.focus.position, direction=direction, distance=self.camdistance, ignore=self.ignore_traverse)
        if ray.hit:
            dist = math.dist(ray.world_point, self.focus.position)
            camera.z = -1 * min(self.camdistance, dist)
        else:
            camera.z = -1 * self.camdistance

    def move(self):
        """Adjust self's position by velocity * time since last frame"""
        self.position += self.velocity * time.dt

    def move_to(self, loc):
        """Set player's position"""
        self.position = loc

    def move_focus(self):
        """Called every frame, put focus on self"""
        self.focus.position = self.position + Vec3(0, 0.5 * self.height, 0)