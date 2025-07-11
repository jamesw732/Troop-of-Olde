"""API for handling physics calculations."""
from ursina import *

from .base import PHYSICS_UPDATE_RATE, sqnorm, dot

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
        disp_y = char.max_jump_height / char.max_jump_time * dt
        if char.rem_jump_height - disp_y <= 0:
            disp_y = char.rem_jump_height - disp_y
            char.cancel_jump()
        else:
            char.rem_jump_height -= disp_y
        jump_disp = Vec3(0, disp_y, 0)
    else:
        jump_disp = Vec3(0, 0, 0)
    char.displacement_components["jump"] = jump_disp

def get_displacement(char):
    """Takes the sum of all character's velocity components, multiplies by dt, and applies physics"""
    displacement = sum(list(char.velocity_components.values())) * dt
    if len(char.displacement_components.values()) > 0:
        displacement += sum(list(char.displacement_components.values()))
    if displacement == Vec3(0, 0, 0):
        return displacement
    return apply_physics(char, displacement, ignore=char.ignore_traverse)

# PRIVATE
def apply_physics(char, displacement, ignore=[]):
    """Takes a character displacement and returns a collision-modified displacement"""
    disp_norm = distance((0, 0, 0), displacement)
    ray = raycast(char.world_position, direction=displacement, distance=disp_norm, ignore=ignore)
    if ray.hit:
        normal = ray.world_normal
        if normal.normalized()[1] <= 0.2:
            # Intersection of the plane ax + by + cz = 0 with y = 0
            direction = Vec3(normal[2], 0, -normal[0]).normalized()
            displacement = direction * dot(direction, displacement.normalized()) * disp_norm
            char.grounded = True
        else:
            if not char.grounded:
                char.grounded = True
                displacement = ray.world_point - char.world_position + Vec3(0, 1e-3, 0)
                return displacement
            # Intersection of the plane ax + by + cz = 0 with the plane defined by (0, 0, 0),
            # (0, 1, 0), and original displacement
            direction = Vec3(displacement[0] * normal[1],
                             -displacement[2] * normal[2] - displacement[0] * normal[0],
                             displacement[2] * normal[1]).normalized()
            displacement = direction * disp_norm
    elif char.grounded:
        down_ray = raycast(char.world_position, direction=char.down, distance=0.2, ignore=ignore)
        if not down_ray.hit:
            char.grounded = False
    # Block upward movement if jumping into a ceiling
    if displacement[1] < 0:
        return displacement
    # Cast ray from top of model, rather than bottom like in handle_collision
    pos = char.position + Vec3(0, char.height, 0)
    ceiling = raycast(pos, direction=(0, 1, 0), distance=displacement[1],
                      ignore=ignore)
    if ceiling.hit:
        displacement[1] = 0
    return displacement