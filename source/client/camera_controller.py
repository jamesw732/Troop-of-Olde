from ursina import *


class CameraController(Entity):
    def __init__(self, character):
        super().__init__()
        self.character = character
        self.focus = Entity(
            parent=self.character,
            world_rotation_y=0,
            world_scale = (1, 1, 1),
            position = Vec3(0, 0.75, 0)
        )
        self.camdistance = 20
        camera.parent = self.focus
        camera.position = (0, 0, -1 * self.camdistance)

        self.prev_mouse_position = mouse.position

    def update(self):
        max_vert_rotation = 80
        self.focus.rotation_x = clamp(self.focus.rotation_x, -max_vert_rotation, max_vert_rotation)
        # Adjust camera zoom
        direction = camera.world_position - self.focus.world_position
        ray = raycast(self.focus.world_position, direction=direction, distance=self.camdistance,
                      ignore=self.character.ignore_traverse)
        if ray.hit:
            dist = math.dist(ray.world_point, self.focus.world_position)
            camera.z = -1 * min(self.camdistance, dist)
        else:
            camera.z = -1 * self.camdistance

    def handle_updown_keyboard_rotation(self, updown, dt):
        """Handles up/down arrow key rotation."""
        self.focus.rotate(Vec3(updown * 100 * dt, 0, 0))

    def update_mouse_x_rotation(self, amt):
        """Updates self.focus.rotation_x with rotation obtained from mouse movement"""
        self.focus.rotation_x += amt

    def zoom_in(self):
        self.camdistance = max(self.camdistance - 1, 0)

    def zoom_out(self):
        self.camdistance = min(self.camdistance + 1, 75)
