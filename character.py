"""Represents the physical player/npc entities in game"""
from mob import *
from ursina import *
import numpy

class Character(Entity):
    def __init__(self, name, *args, mob=None, **kwargs):
        super().__init__(*args, **kwargs)
        if mob:
            self.mob = mob
        else:
            self.mob = Mob(self, speed=20)
        self.name = name

        self.height = self.scale_y

        self.velocity = Vec3(0, 0, 0)
        self.velocity_components = {}

        self.jumping = False
        self.grounded = False
        self.grav = 0

        self.max_jump_height = self.height * 1.5
        self.rem_jump_height = self.max_jump_height
        self.max_jump_time = 0.3
        self.rem_jump_time = self.max_jump_time

        self.traverse_target = scene
        self.ignore_traverse = [self]

    def update(self):
        self.handle_movement()

    def handle_movement(self):
        """Combines all movement inputs into one velocity vector, then handles collision and grounding and moves in just one call."""
        # Get the character-only velocity items
        self.set_gravity_vel()
        self.set_jump_vel()
        # Combine them all, there will likely be others besides gravity and jumping
        self.velocity = sum(list(self.velocity_components.values()))
        # If components was empty, we get an int, so convert to zero vector
        if type(self.velocity) is int:
            self.velocity = Vec3(0, 0, 0)

        self.handle_grounding()
        self.handle_collision()
        self.handle_upward_collision()

        self.position += self.velocity * time.dt

    def set_gravity_vel(self):
        """If not grounded and not jumping, subtract y (linear in time) from velocity vector"""
        if not self.grounded and not self.jumping:
            self.grav -= 1
        elif self.grounded:
            self.grav = 0
        self.velocity_components["gravity"] = Vec3(0, self.grav, 0)

    def set_jump_vel(self):
        """If jumping, add some y to velocity vector"""
        if self.jumping:
            speed = self.max_jump_height / self.max_jump_time
            if self.rem_jump_height - speed * time.dt <= 0:
                speed = self.rem_jump_height / self.max_jump_time
                self.cancel_jump()
            else:
                self.rem_jump_height -= speed * time.dt
            jump_vel = Vec3(0, speed, 0)
        else:
            jump_vel = Vec3(0, 0, 0)
        self.velocity_components["jump"] = jump_vel

    def handle_grounding(self):
        """Handles logic for whether the character is grounded or not.
        Doesn't move the character at all, just handles logic for whether or not the player is grounded"""
        if self.velocity[1] > 0:
            self.grounded = False
        elif self.velocity[1] == 0:
            ground = raycast(self.position, direction=(0, -1, 0), distance=0.01, ignore=self.ignore_traverse)
            self.grounded = ground.hit
        else:
            ground = raycast(self.position, direction=(0, -1, 0), distance=abs(self.velocity[1] * time.dt), ignore=self.ignore_traverse)
            if ground.hit:
                self.grounded = True

    def handle_collision(self):
        """Handles most of the collision logic."""
        norm = distance((0, 0, 0), self.velocity) * time.dt
        pos = self.position
        collision_check = raycast(pos, direction=self.velocity, distance=norm, ignore=self.ignore_traverse)
        if collision_check.hit:
            normal = collision_check.world_normal
            if numpy.dot(normal, self.velocity) < 0:
                # Project velocity onto normal of colliding entity
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
        # Cast ray from top of model, rather than bottom like in handle_collision
        pos = self.position + Vec3(0, self.height, 0)
        ceiling = raycast(pos, direction=(0, 1, 0), distance=self.velocity[1] * time.dt, ignore=self.ignore_traverse)
        if ceiling.hit:
            self.velocity[1] = 0

    def start_jump(self):
        """Set self.jumping"""
        if self.grounded:
            self.jumping = True

    def cancel_jump(self):
        """Reset self.jumping, remaining jump height"""
        self.jumping = False
        self.rem_jump_height = self.max_jump_height