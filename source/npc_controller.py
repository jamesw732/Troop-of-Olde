"""Defines all 'physical' NPC behavior"""

from ursina import Entity

class NPC_Controller(Entity):
    def __init__(self, character, player=None):
        super().__init__()
        self.character = character
        self.character.type = "npc"