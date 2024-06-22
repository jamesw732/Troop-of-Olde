from ursina import *
import numpy

from .gamestate import *


# PUBLIC
# Update this to expand PhysicalState
phys_state_attrs = {
    "speed": float,
    "model": str,
    "scale": Vec3,
    "origin": Vec3,
    "collider": str,
    "position": Vec3,
    "rotation": Vec3,
    "color": str,

    "name": str,
    "type": str,
    "target": int,
    "in_combat": bool,
}

class PhysicalState:
    """The real intention behind this class is to encompass client-authoritative
    Character attributes. Inclusions are pretty loose; for example in_combat seems
    like it should belong in CombatState but it makes more sense for it to be
    client-authoritative.."""
    def __init__(self, char=None, **kwargs):
        # If a character was passed, take its attributes
        if char is not None:
            for attr in phys_state_attrs:
                if hasattr(char, attr):
                    val = getattr(char, attr)
                    # Only include attrs intentionally set
                    if val is not None:
                        if attr in ["collider", "color", "model"]:
                            # Ursina objects exist in PhysicalState as string names
                            val = val.name
                        setattr(self, attr, val)
        # Otherwise, read the attributes straight off
        else:
            for attr in phys_state_attrs:
                if attr in kwargs:
                    setattr(self, attr, kwargs[attr])

    def __str__(self):
        return str({attr: getattr(self, attr)
                for attr in phys_state_attrs if hasattr(self, attr)})

def handle_movement(char):
    """Main physics method which combines all character velocities into one
    vector, then handles collision and grounding and updates position"""
    set_gravity_vel(char)
    set_jump_vel(char)

    velocity = sum(list(char.velocity_components.values()))

    if type(velocity) is int:
        velocity = Vec3(0, 0, 0)

    handle_grounding(char, velocity)
    velocity = handle_collision(char, velocity)
    velocity = handle_upward_collision(char, velocity)

    char.position += velocity * time.dt


# PRIVATE
def set_gravity_vel(char):
    """If not grounded and not jumping, subtract y (linear in time) from velocity vector"""
    grav = char.velocity_components.get("gravity", Vec3(0, 0, 0))
    if not char.grounded and not char.jumping:
        grav -= Vec3(0, 100 * time.dt, 0)
    elif char.grounded:
        grav = Vec3(0, 0, 0)
    char.velocity_components["gravity"] = grav # Try deleting this line


def set_jump_vel(char):
    """If jumping add, some y to jump velocity vector"""
    # Meant to simulate the actual act of jumping, ie feet still touching ground
    if char.jumping:
        speed = char.max_jump_height / char.max_jump_time
        if char.rem_jump_height - speed * time.dt <= 0:
            speed = char.rem_jump_height / char.max_jump_time
            char.cancel_jump()
        else:
            char.rem_jump_height -= speed * time.dt
        jump_vel = Vec3(0, speed, 0)
    else:
        jump_vel = Vec3(0, 0, 0)
    char.velocity_components["jump"] = jump_vel


def handle_grounding(char, velocity):
    if velocity[1] > 0:
        char.grounded = False
    elif velocity[1] == 0:
        ground = raycast(char.position, direction=(0, -1, 0), distance=0.01, ignore=char.ignore_traverse)
        char.grounded = ground.hit
    else:
        ground = raycast(char.position, direction=(0, -1, 0),
                         distance=abs(velocity[1] * time.dt),
                         ignore=char.ignore_traverse)
        if ground.hit:
            char.grounded = True


def handle_collision(char, velocity):
    """Handles feet collision logic"""
    dist = distance((0, 0, 0), velocity) * time.dt
    collision_check = raycast(char.position, direction=velocity, distance=dist, ignore=char.ignore_traverse)
    if collision_check.hit:
        normal = collision_check.world_normal
        if numpy.dot(normal, velocity) < 0:
            # Note this is different from character speed if multiple velocity components
            speed = distance(Vec3.zero, velocity)
            # Project velocity onto normal of colliding entity
            # This is not correct.
            velocity = velocity - (numpy.dot(normal, velocity)) * normal
            # Match old speed
            velocity = velocity.normalized() * speed
            # Make sure new velocity doesn't pass through any entities, ie concave case.
            # For now, we just don't move at all, but eventually can improve this.
            dist2 = distance((0, 0, 0), velocity) * time.dt
            ray = raycast(char.position, direction=velocity, distance=dist2, ignore=char.ignore_traverse)
            if ray.hit:
                velocity = Vec3(0, 0, 0)
    return velocity


def handle_upward_collision(char, velocity):
    """Blocks upward movement when jumping into a ceiling"""
    if velocity[1] < 0:
        return velocity
    # Cast ray from top of model, rather than bottom like in handle_collision
    pos = char.position + Vec3(0, char.height, 0)
    ceiling = raycast(pos, direction=(0, 1, 0), distance=velocity[1] * time.dt,
                      ignore=char.ignore_traverse)
    if ceiling.hit:
        velocity[1] = 0
    return velocity