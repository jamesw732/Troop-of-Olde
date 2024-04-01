"""Controls all NPC collision and movement"""

from ursina import *
from mob import Mob

class NPC(Entity):
    def __init__(self, name, *args, mob=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.height = self.scale_y
        if mob:
            self.mob = mob
        else:
            self.mob = Mob(self)
        self.namelabel = self.make_name_text()
    
    def make_name_text(self):
        return Text(self.name, parent=scene, scale=10, origin=(0, 0, 0), position=self.position + Vec3(0, self.height + 1, 0))

    def rotate_namelabel(self, pos):
        self.namelabel.look_at(pos)
        self.namelabel.rotation_x *= -1
        self.namelabel.rotation_y += 180
        self.namelabel.rotation_z = 0