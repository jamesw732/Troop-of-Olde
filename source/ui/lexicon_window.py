from ursina import *

from .base import *
from .header import *
from ..gamestate import gs

class LexiconWindow(Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.player = gs.pc

        # This is used to normalize lengths relative to the width/height of the ItemsWindow
        # Given a width/length, multiply the length by window_wh_ratio to get the correct
        # length relative to the width
        window_wh_ratio = self.world_scale_x / self.world_scale_y
        # How far away from the edge to put the subcontainers
        edge_margin = 0.05

        page_width = 0.4
        page_grid_size = (3, 5)
        box_spacing = 0.1
        # Compute height of pages WRT window
        x = page_width / (page_grid_size[0] + box_spacing * (page_grid_size[0] - 1))
        y = x * window_wh_ratio
        page_height = y * (page_grid_size[1] + box_spacing * (page_grid_size[1] - 1))
        # height of equip frame relative to the width
        page_scale = Vec3(page_width, page_height, 1)
        self.page1 = Entity(parent=self, origin=(-.5, .5),
                                        position=(edge_margin, -edge_margin, -1),
                                        scale=page_scale)
        self.page2 = Entity(parent=self, origin=(-.5, .5),
                                        position=(3*edge_margin + page_width, -edge_margin, -1),
                                        scale=page_scale)
        # Compure the scale of the boxes with respect to the frame
        box_w = 1 / (page_grid_size[0] + box_spacing * (page_grid_size[0] - 1))
        box_h = 1 / (page_grid_size[1] + box_spacing * (page_grid_size[1] - 1))

        box_scale = Vec3(box_w, box_h, 1)

        positions = [Vec3(i, -j, -1)
                     for j in range(page_grid_size[1])
                     for i in range(page_grid_size[0])]

        self.page1_boxes = [PowerBox(slot=str(i), container_name="inventory",
                                            parent=self.page1,
                                            position=pos * box_scale * (1 + box_spacing),
                                            scale=box_scale, color=slot_color)
                            for i, pos in enumerate(positions)]
        self.page2_boxes = [PowerBox(slot=str(i), container_name="inventory",
                                            parent=self.page2,
                                            position=pos * box_scale * (1 + box_spacing),
                                            scale=box_scale, color=slot_color)
                            for i, pos in enumerate(positions)]
        for slot in self.page1_boxes:
            grid(slot, num_rows=1, num_cols=1, color=color.black)
        for slot in self.page2_boxes:
            grid(slot, num_rows=1, num_cols=1, color=color.black)

    def enable_colliders(self):
        pass

    def disable_colliders(self):
        pass

class PowerBox(Entity):
    def __init__(self, *args, container=None, slot=None, container_name="", **kwargs):
        super().__init__(*args, origin=(-.5, .5), model='quad', collider='box', **kwargs)
        self.container_name = container_name
        self.container = getattr(gs.pc, container_name)
        self.slot = slot
        self.itemicon = None
