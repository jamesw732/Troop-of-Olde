from ursina import *
import json
import copy

from ..item import Item, Container
from ..gamestate import gs

class ServerItem(Item):
    def __init__(self, item_id):
        # Set the instance ID. Server needs to externally transmit this upon item creation.
        self.inst_id = gs.network.item_inst_id_ct
        gs.network.item_inst_id_ct += 1
        super().__init__(item_id, self.inst_id)


class ServerContainer(Container):
    def __init__(self, name, items):
        container_id = gs.network.container_inst_id_ct
        gs.network.container_inst_id_ct += 1
        super().__init__(container_id, name, items)
