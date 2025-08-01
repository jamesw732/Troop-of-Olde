from ursina import *

from .items import *


class ItemsManager(Entity):
    """Class with dedicated access to all ItemFrames and ItemIcons"""
    def __init__(self, char):
        super().__init__()
        self.char = char
        self.inst_id_to_item_icon = {}
        self.item_frames = {}

    def make_item_frame(self, grid_size, container, slot_labels=[], **kwargs):
        """Creates an ItemFrame and adds it to self.item_frames."""
        frame = ItemFrame(self.char, grid_size, container, slot_labels=slot_labels, **kwargs)
        self.item_frames[container.name] = frame
        for i, box in enumerate(frame.boxes):
            item = container[i]
            icon = self.make_item_icon(item, box)
        return frame

    def make_item_icon(self, item, box):
        """Creates an ItemIcon and adds it to self.inst_id_to_item_icon."""
        if item is None:
            icon = None
        else:
            icon = ItemIcon(item, parent=box, scale=(1, 1), position=(0, 0, -2))
            self.inst_id_to_item_icon[item.inst_id] = icon
        box.set_item_icon(icon)
        return icon

    def update_item_icons(self):
        """Update position of item icons based on current state of containers"""
        for frame in self.item_frames.values():
            for slot, box in enumerate(frame.boxes):
                item = frame.container[slot]
                if item is None:
                    icon = None
                else:
                    icon = self.inst_id_to_item_icon[item.inst_id]
                box.set_item_icon(icon)


