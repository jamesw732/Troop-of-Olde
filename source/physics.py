"""API for handling physics calculations."""
from ursina import *
import numpy

from .base import PHYSICS_UPDATE_RATE
from .gamestate import gs

dt = PHYSICS_UPDATE_RATE

# PUBLIC
def set_gravity_vel(char):
    """If not grounded and not jumping, subtract y (linear in time) from velocity vector"""
    grav = char.velocity_components.get("gravity", Vec3(0, 0, 0))
    if not char.grounded and not char.jumping:
        grav -= Vec3(0, 5, 0)
    elif char.grounded:
        grav = Vec3(0, 0, 0)
    char.velocity_components["gravity"] = grav

def set_jump_vel(char):
    """If jumping add, some y to jump velocity vector"""
    # Meant to simulate the actual act of jumping, ie feet still touching ground
    if char.jumping:
        speed = char.max_jump_height / char.max_jump_time * dt
        if char.rem_jump_height - speed <= 0:
            speed = char.rem_jump_height / char.max_jump_time * dt
            char.cancel_jump()
        else:
            char.rem_jump_height -= speed
        jump_vel = Vec3(0, speed / dt, 0)
    else:
        jump_vel = Vec3(0, 0, 0)
    char.velocity_components["jump"] = jump_vel

def get_displacement(char):
    """Takes the sum of all character's velocity components, multiplies by dt, and applies physics"""
    displacement = sum(list(char.velocity_components.values())) * dt
    # Internal functions of apply_physics should be completely agnostic of dt
    return apply_physics(char, displacement)

# PRIVATE
def apply_physics(char, displacement):
    """Takes a character displacement and applies physics functions to ensure it can be applied"""
    if displacement[1] <= 0:
        handle_grounding(char, displacement)
    displacement = handle_collision(char, displacement)
    displacement = handle_upward_collision(char, displacement)
    return displacement

def handle_grounding(char, displacement):
    """Determine whether character is on the ground or not. Kills y displacement if grounded."""
    ignore_traverse = char.ignore_traverse
    # This doesn't seem to provide any sort of performance improvement
    # if gs.ui:
    #     ignore_traverse += gs.ui.colliders
    ground = raycast(char.world_position + (0, char.height, 0), direction=char.down,
                     ignore=ignore_traverse)
    if not ground.hit:
        char.grounded = False
        return
    # If ground is within next timestep, we're grounded.
    if ground.distance <= char.height + max(0.01, abs(displacement[1])):
        # print("Grounding")
        char.grounded = True
        char.world_y = ground.world_point[1] + 1e-5
        displacement[1] = 0
    else:
        char.grounded = False

def handle_collision(char, displacement, depth=0):
    """Handles feet collision logic.

    If displacement hits a surface, "project" displacement along that surface, then recursively
    check again."""
    # It's concave, don't try to handle it, just stop
    if depth > 3:
        return Vec3(0, 0, 0)
    dist = distance((0, 0, 0), displacement)
    collision_check = raycast(char.position, direction=displacement, distance=dist, ignore=char.ignore_traverse)
    if collision_check.hit:
        normal = collision_check.world_normal
        speed = distance(Vec3.zero, displacement)
        # It's a wall
        if abs(normal.normalized()[1]) <= 0.4:
            # Do normal projection formula
            new_displacement = displacement - (numpy.dot(normal, displacement)) * normal
            new_displacement[1] = 0
        # It's a slope
        else:
            point1 = collision_check.world_point
            plane_const = numpy.dot(normal, point1)
            # take new x and z coordinates as if the surface didn't exist
            x2 = displacement[0] + point1[0]
            z2 = displacement[2] + point1[2]
            # find the expected y coordinate from the x and z
            y2 = (plane_const - x2 * normal[0] - z2 * normal[2]) / normal[1]
            point2 = Vec3(x2, y2, z2)
            # new point is the right direction but wrong distance, re-scale
            new_displacement = (point2 - point1).normalized() * speed
        return handle_collision(char, new_displacement, depth + 1)
    else:
        return displacement


def handle_upward_collision(char, displacement):
    """Blocks upward movement when jumping into a ceiling"""
    if displacement[1] < 0:
        return displacement
    # Cast ray from top of model, rather than bottom like in handle_collision
    pos = char.position + Vec3(0, char.height, 0)
    ceiling = raycast(pos, direction=(0, 1, 0), distance=displacement[1],
                      ignore=char.ignore_traverse)
    if ceiling.hit:
        displacement[1] = 0
    return displacement