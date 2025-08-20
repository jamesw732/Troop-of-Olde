"""API for handling physics calculations."""
from ursina import *

from .base import PHYSICS_UPDATE_RATE, sqnorm, dot

dt = PHYSICS_UPDATE_RATE

# PUBLIC
def set_gravity_vel(char):
    """If not grounded and not jumping, subtract y from velocity vector"""
    grav = char.velocity_components.get("gravity", Vec3(0, 0, 0))
    if not char.grounded:
        grav -= Vec3(0, 100, 0) * dt
        # Don't use fixed value because dt might change
        # grav -= Vec3(0, 5, 0)
    else:
        grav = Vec3(0, 0, 0)
    char.velocity_components["gravity"] = grav

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
            char.cancel_jump()
        else:
            if not char.grounded:
                char.grounded = True
                char.cancel_jump()
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
    pos = char.position + Vec3(0, char.scale_y, 0)
    ceiling = raycast(pos, direction=(0, 1, 0), distance=displacement[1],
                      ignore=ignore)
    if ceiling.hit:
        displacement[1] = 0
    return displacement