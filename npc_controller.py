"""Defines all 'physical' NPC behavior"""

from ursina import *
from mob import Mob

class NPC_Controller(Entity):
    def __init__(self, character):
        super().__init__()
        self.character = character
        self.namelabel = self.make_name_text()

    def make_name_text(self):
        return Text(self.character.name, parent=scene, scale=10, origin=(0, 0, 0), position=self.character.position + Vec3(0, self.character.height + 1, 0))

    def rotate_namelabel(self, direction):
        """Rotate namelabel to be parallel with player and camera.
        dir: player world position - camera world position"""
        self.namelabel.look_at(direction + self.namelabel.world_position)
        self.namelabel.rotation_z = 0