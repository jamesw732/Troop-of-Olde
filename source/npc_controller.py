"""Defines all 'physical' NPC behavior"""

from ursina import *

class NPC_Controller(Entity):
    def __init__(self, character, player):
        super().__init__()
        self.character = character
        self.character.type = "npc"
        # self.character.namelabel = self.make_name_text()
        # self.player = player

    # def update(self):
    #     self.rotate_namelabel(self.player.world_position - camera.world_position)

    # def make_name_text(self):
    #     return Text(self.character.name, parent=scene, scale=10, origin=(0, 0, 0), position=self.character.position + Vec3(0, self.character.height + 1, 0))

    # def rotate_namelabel(self, direction):
    #     """Rotate namelabel to be parallel with player and camera.
    #     dir: player world position - camera world position"""
    #     self.character.namelabel.look_at(direction + self.character.namelabel.world_position)
    #     self.character.namelabel.rotation_z = 0