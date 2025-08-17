from ursina import *


class NameLabelSystem(Entity):
    def __init__(self, gamestate):
        super().__init__()
        self.uuid_to_labl = gamestate.uuid_to_labl

    def create_namelabel(self, char):
        self.uuid_to_labl[char.uuid] = NameLabel(char)

    def update(self):
        for namelabel in self.uuid_to_labl.values():
            namelabel.fix_rotation()

    def destroy_labl(self, uuid):
        namelabel = self.uuid_to_labl[uuid]
        destroy(namelabel)
        del namelabel.char
        del self.uuid_to_labl[uuid]


class NameLabel(Text):
    def __init__(self, char):
        """Creates a namelabel above a character
        
        Todo: Change parent to character"""
        super().__init__(char.cname, parent=char, scale=6, origin=(0, 0, 0), y=1.4)
        self.char = char

    def fix_rotation(self):
        """Aim the namelabel at the player with the right direction"""
        if self.char.position:
            self.look_at(camera, axis=Vec3.back)
            self.world_rotation_z = 0
