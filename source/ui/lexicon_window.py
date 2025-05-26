from ursina import *

from .base import *
from .header import *
from ..gamestate import gs

class LexiconWindow(Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # This is used to normalize lengths relative to the width/height of the ItemsWindow
        # Given a width/length, multiply the length by window_wh_ratio to get the correct
        # length relative to the width
        window_wh_ratio = self.world_scale_x / self.world_scale_y
        # How far away from the edge to put the subcontainers
        edge_margin = 0.05

        page_width = 0.9
        page_grid_size = (6, 5)
        box_spacing = 0.1
        # Compute height of page WRT window
        x = page_width / (page_grid_size[0] + box_spacing * (page_grid_size[0] - 1))
        y = x * window_wh_ratio
        page_height = y * (page_grid_size[1] + box_spacing * (page_grid_size[1] - 1))
        # height of equip frame relative to the width
        page_scale = Vec3(page_width, page_height, 1)
        self.page = Entity(parent=self, origin=(-.5, .5),
                                        position=(edge_margin, -edge_margin, -1),
                                        scale=page_scale)
        # Compure the scale of the boxes with respect to the frame
        box_w = 1 / (page_grid_size[0] + box_spacing * (page_grid_size[0] - 1))
        box_h = 1 / (page_grid_size[1] + box_spacing * (page_grid_size[1] - 1))

        box_scale = Vec3(box_w, box_h, 1)

        positions = [Vec3(i, -j, -1)
                     for j in range(page_grid_size[1])
                     for i in range(page_grid_size[0])]

        self.boxes = [PowerBox(gs.pc.powers, i,
                                parent=self.page,
                                position=pos * box_scale * (1 + box_spacing),
                                scale=box_scale, color=slot_color)
                        for i, pos in enumerate(positions)]
        for slot in self.boxes:
            grid(slot, num_rows=1, num_cols=1, color=color.black)

    def enable_colliders(self):
        # Is it possible to accomplish this without looping?
        for box in self.boxes:
            if box.icon is not None:
                box.icon.collision = True

    def disable_colliders(self):
        for box in self.boxes:
            if box.icon is not None:
                box.icon.collision = False

    def start_gcd_animation(self):
        nonempty_boxes = (box for box in self.boxes if box.icon is not None)
        for box in nonempty_boxes:
            box.gcd_overlay = Timer(parent=box, origin=(-.5, .5), position=(0, 0, -2), size=(1, 1),
                                    model='quad', color=color.gray, alpha=0.6,
                                    scale_x = 1 - gs.pc.gcd_timer / gs.pc.gcd)

class Timer(Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def update(self):
        self.scale_x = 1 - gs.pc.gcd_timer / gs.pc.gcd
        if self.scale_x <= 0:
            destroy(self)
            self.parent.gcd_overlay = None

class PowerBox(Entity):
    def __init__(self, powers_list, slot, *args, **kwargs):
        super().__init__(*args, origin=(-.5, .5), model='quad', **kwargs)
        self.powers_list = powers_list
        self.slot = slot
        self.icon = None
        self.gcd_overlay = None
        power = powers_list[self.slot]
        if power is not None:
            self.icon = PowerIcon(power, parent=self, scale=(1, 1), texture=power.icon,
                      position=(0, 0, -1), alpha=0.4)


class PowerIcon(Entity):
    def __init__(self, power, *args, **kwargs):
        super().__init__(*args, origin=(-.5, .5), model='quad', collider='box', **kwargs)
        self.power = power

    def on_click(self):
        tgt = self.power.get_target(gs.pc)
        if gs.pc.get_on_gcd():
            if gs.pc.next_power is self.power:
                # Attempted to queue an already queued power, just remove it
                gs.pc.next_power = None
            else:
                self.power.queue(gs.pc)
        else:
            self.power.client_use_power(gs.pc, tgt)
            gs.network.peer.request_use_power(gs.network.server_connection, self.power.power_id)
