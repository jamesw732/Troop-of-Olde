from ursina import *
import numpy


# PUBLIC
def handle_movement(char):
    """Main physics method which combines all character velocities into one
    vector, then handles collision and grounding and updates position"""
    set_gravity_vel(char)
    set_jump_vel(char)

    velocity = sum(list(char.velocity_components.values()))

    if velocity[1] <= 0:
        handle_grounding(char, velocity)

    if velocity != Vec3.zero:
        velocity = handle_collision(char, velocity)
        velocity = handle_upward_collision(char, velocity)

    char.position += velocity * time.dt


# PRIVATE
def set_gravity_vel(char):
    """If not grounded and not jumping, subtract y (linear in time) from velocity vector"""
    grav = char.velocity_components.get("gravity", Vec3(0, 0, 0))
    if not char.grounded and not char.jumping:
        grav -= Vec3(0, 75 * time.dt, 0)
    elif char.grounded:
        grav = Vec3(0, 0, 0)
    char.velocity_components["gravity"] = grav


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
    """Determine whether character is on the ground or not. Kills y velocity if grounded."""
    ground = raycast(char.world_position + (0, char.height, 0), direction=char.down,
                     ignore=char.ignore_traverse, debug=True)
    if not ground.hit:
        char.grounded = False
        return
    # If ground is within next timestep, we're grounded.
    if ground.distance <= char.height + max(0.01, abs(velocity[1] * time.dt)):
        # print("Grounding")
        char.grounded = True
        char.world_y = ground.world_point[1] + 1e-5
        velocity[1] = 0
    else:
        # print("Falling")
        char.grounded = False

def handle_collision(char, velocity, depth=0):
    """Handles feet collision logic."""
    # It's concave, don't try to handle it, just stop
    if depth > 3:
        return Vec3(0, 0, 0)
    dist = distance((0, 0, 0), velocity) * time.dt
    collision_check = raycast(char.position, direction=velocity, distance=dist, ignore=char.ignore_traverse)
    if collision_check.hit:
        normal = collision_check.world_normal
        speed = distance(Vec3.zero, velocity)
        # It's a wall
        if abs(normal.normalized()[1]) <= 0.2:
            new_velocity = velocity - (numpy.dot(normal, velocity)) * normal
            new_velocity = new_velocity
        # It's a slope
        else:
            point1 = collision_check.world_point
            plane_const = numpy.dot(normal, point1)
            x2 = velocity[0] * time.dt + point1[0]
            z2 = velocity[2] * time.dt + point1[2]
            y2 = (plane_const - x2 * normal[0] - z2 * normal[2]) / normal[1]
            point2 = Vec3(x2, y2, z2)
            new_velocity = (point2 - point1).normalized() * speed
        return handle_collision(char, new_velocity, depth + 1)
    else:
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