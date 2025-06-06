"""API for handling physics calculations."""
from ursina import *
import numpy

from .base import PHYSICS_UPDATE_RATE, sqnorm
from .gamestate import gs

dt = PHYSICS_UPDATE_RATE

# PUBLIC
def set_gravity_vel(char):
    """If not grounded and not jumping, subtract y (linear in time) from velocity vector"""
    grav = char.velocity_components.get("gravity", Vec3(0, 0, 0))
    if not char.grounded and not char.jumping:
        grav -= Vec3(0, 5, 0)
    else:
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
    if not char.grounded:
        displacement = handle_ungrounded_collision(char, displacement)
        displacement = handle_upward_collision(char, displacement)
    else:
        displacement = handle_grounded_collision(char, displacement)
    return displacement

def handle_ungrounded_collision(char, displacement):
    """Determine whether character's displacement will result in collision.

    Assumes char.grounded is False
    Adjusts and returns displacement that would cause character to not clip through floor"""
    ray = raycast(char.world_position, direction=displacement, ignore=char.ignore_traverse)
    if ray.hit and ray.distance ** 2 <= sqnorm(displacement):
        displacement = ray.world_point - char.world_position + Vec3(0, 1e-3, 0)
        char.grounded = True
    return displacement

def handle_grounded_collision(char, displacement):
    """Handle collision logic when grounded

    Assumes char.grounded is True"""
    down_ray = raycast(char.world_position, direction=char.down, ignore=char.ignore_traverse)
    ray = raycast(char.world_position, direction=displacement, ignore=char.ignore_traverse)
    disp_norm = distance((0, 0, 0), displacement)
    if ray.hit and ray.distance < disp_norm:
        normal = ray.world_normal
        if normal.normalized()[1] <= 0.2:
            # Intersection of the plane ax + by + cz = 0 with y = 0
            direction = Vec3(normal[2], 0, -normal[0]).normalized()
            displacement = direction * disp_norm * numpy.dot(direction, displacement)
        else:
            point1 = ray.world_point
            plane_const = numpy.dot(normal, point1)
            # take new x and z coordinates as if the surface didn't exist
            x2 = displacement[0] + point1[0]
            z2 = displacement[2] + point1[2]
            # find the expected y coordinate from the x and z
            y2 = (plane_const - x2 * normal[0] - z2 * normal[2]) / normal[1]
            point2 = Vec3(x2, y2, z2)
            # new point is the right direction but wrong distance, re-scale
            displacement = (point2 - point1).normalized() * disp_norm
    elif not down_ray.hit or down_ray.distance > 0.2:
        char.grounded = False
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