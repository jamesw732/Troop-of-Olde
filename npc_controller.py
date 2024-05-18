"""Defines all 'physical' NPC behavior"""

from ursina import *
from mob import Mob

class NPC_Controller(Entity):
    def __init__(self, character):
        super().__init__()
        self.character = character
        self.namelabel = self.make_name_text()
    
    def update(self):
        self.rotate_namelabel(camera.world_position)

    def make_name_text(self):
        return Text(self.name, parent=scene, scale=10, origin=(0, 0, 0), position=self.character.position + Vec3(0, self.character.height + 1, 0))

    def rotate_namelabel(self, pos):
        self.namelabel.look_at(pos)
        self.namelabel.rotation_x *= -1
        self.namelabel.rotation_y += 180
        self.namelabel.rotation_z = 0