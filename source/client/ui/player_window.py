from ursina import *

from .base import *
from .items_window import *
from .skills_window import *
from .stats_window import *
from .window import UIWindow


class PlayerWindow(UIWindow):
    def __init__(self, char):
        self.char = char
        scale = (0.24, 0.45)
        global window
        super().__init__(position=(0.5 * window.aspect_ratio - 0.01 - scale[0], scale[1] - 0.49), scale=scale,
                         bg_alpha = 200/255, header_ratio=0.05)

        margin_length = 0.025
        button_width = 0.3
        button_height = 0.08
        button_scale = (button_width, button_height)
        # tab_scale = (.95, .8725)
        # tab_pos = (.025, -.1, -1)
        subheader_height = 3 * margin_length + button_height
        tab_scale = (1 - 2 * margin_length, 1 - subheader_height)
        tab_pos = (.025, -subheader_height + margin_length, -1)

        # Make Items window/button
        self.items = ItemsWindow(self.char, parent=self.body, model='quad', origin=(-.5, .5),
                                 scale=tab_scale, position=tab_pos,
                                 color=window_fg_color)
        self.itemsbutton = Entity(
            parent=self.body, model='quad', origin=(-.5, .5),
            position=(margin_length, -margin_length, -1), scale=button_scale,
            color=header_color, collider="box"
        )
        self.itemsbutton.on_click = lambda: self.open_window("open items")
        Text(parent=self.itemsbutton, text="Items", world_scale=(15, 15),
             origin=(0, 0), position=(0.5, -0.5, -2))
        # Make Skills window/button
        self.skills = SkillsWindow(self.char, parent=self.body, model='quad', origin=(-.5, .5),
                                 scale=tab_scale, position=tab_pos,
                                 color=window_fg_color)
        self.skillsbutton = Entity(
            parent=self.body, model='quad', origin=(-.5, .5),
            position=(button_width + 2 * margin_length, -margin_length, -1), scale=button_scale,
            color=header_color, collider="box"
        )
        self.skillsbutton.on_click = lambda: self.open_window("open skills")
        Text(parent=self.skillsbutton, text="Skills", world_scale=(15, 15),
             origin=(0, 0), position=(0.5, -0.5, -2))
        # Make Stats window/button
        self.stats = StatsWindow(self.char, parent=self.body, model='quad', origin=(-.5, .5),
                                 scale=tab_scale, position=tab_pos,
                                 color=window_fg_color)
        self.statsbutton = Entity(
            parent=self.body, model='quad', origin=(-.5, .5),
            position=(2 * button_width + 3 * margin_length, -margin_length, -1), scale=button_scale,
            color=header_color, collider="box"
        )
        self.statsbutton.on_click = lambda: self.open_window("open stats")
        Text(parent=self.statsbutton, text="Stats", world_scale=(15, 15),
             origin=(0, 0),position=(0.5, -0.5, -2))

        self.input_to_interface = {
            "open items": self.items,
            "open skills": self.skills,
            "open stats": self.stats}

        self.input_to_button = {
            "open items": self.itemsbutton,
            "open skills": self.skillsbutton,
            "open stats": self.statsbutton
        }

        self.active_tab = self.items
        self.active_button = self.itemsbutton
        self.active_button.color = active_button_color
        for window in [self.skills, self.stats]:
            window.visible = False

    def input(self, key):
        super().input(key)
        if key in self.input_to_interface:
            self.open_window(key)

    def open_window(self, key):
        new_active_tab = self.input_to_interface[key]
        new_active_button = self.input_to_button[key]
        if new_active_tab == self.active_tab:
            # Close the window
            self.visible = False
            self.active_tab.visible = False
            self.active_tab.disable_colliders()
            self.disable_colliders()
            self.active_tab = None
            self.active_button.color = header_color
            self.active_button = None
        elif not self.visible:
            # Open player window and specified tab, add collider
            self.visible = True
            new_active_tab.visible = True
            self.active_tab = new_active_tab
            self.active_tab.enable_colliders()
            self.enable_colliders()
            new_active_button.color = active_button_color
            self.active_button = new_active_button
        else:
            # Swap to new active tab
            self.active_tab.visible = False
            self.active_tab.disable_colliders()
            self.active_tab = new_active_tab
            self.active_tab.visible = True
            self.active_tab.enable_colliders()
            new_active_button.color = active_button_color
            self.active_button.color = header_color
            self.active_button = new_active_button
            # Will likely need to add colliders for and inventory eventually

    def disable_colliders(self):
        self.collision = False
        for child in [self.items, self.stats]:
            child.disable_colliders()
        self.parent.collision = False
        self.itemsbutton.collision = False
        self.skillsbutton.collision = False
        self.statsbutton.collision = False

    def enable_colliders(self):
        self.parent.collision = True
        self.collision = True
        self.itemsbutton.collision = True
        self.skillsbutton.collision = True
        self.statsbutton.collision = True