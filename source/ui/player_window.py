from ursina import *

from .base import *
from .header import *
from .items_window import *
from .lexicon_window import *
from .skills_window import *
from .stats_window import *

from ..gamestate import gs

class PlayerWindow(Entity):
    def __init__(self):
        self.player = gs.pc.character
        # Make Header
        header = Header(
            position=(0.2, 0.2),
            scale=(.44, .033),
            color=header_color,
            text=self.player.cname,
            ignore_key=lambda c: isinstance(c, Text)
        )
        # Make outer window
        super().__init__(
            parent=header, model='quad', origin=(-.5, .5),
            position=(0, -1), scale=(1, 12),
            color=window_bg_color,
            collider='box'
        )

        margin_length = 0.025
        button_height = 0.08
        # tab_scale = (.95, .8725)
        # tab_pos = (.025, -.1, -1)
        subheader_height = 3 * margin_length + button_height
        tab_scale = (1 - 2 * margin_length, 1 - subheader_height)
        tab_pos = (.025, -subheader_height + margin_length, -1)

        # Make Items window/button
        self.items = ItemsWindow(parent=self, model='quad', origin=(-.5, .5),
                                 scale=tab_scale, position=tab_pos,
                                 color=window_fg_color)
        self.itemsbutton = Entity(
            parent=self, model='quad', origin=(-.5, .5),
            position=(0.025, -margin_length, -1), scale=(0.13, button_height),
            color=header_color, collider="box"
        )
        self.itemsbutton.on_click = lambda: self.open_window("open items")
        Text(parent=self.itemsbutton, text="Items", world_scale=(15, 15),
             origin=(0, 0), position=(0.5, -0.5, -2))
        # Make Lexicon window/button
        self.lex = LexiconWindow(parent=self, model='quad', origin=(-.5, .5),
                                 scale=tab_scale, position=tab_pos,
                                 color=window_fg_color)
        self.lexbutton = Entity(
            parent=self, model='quad', origin=(-.5, .5),
            position=(0.18, -margin_length, -1), scale=(0.17, button_height),
            color=header_color
        )
        self.lexbutton.on_click = lambda: self.open_window("open lexicon")
        Text(parent=self.lexbutton, text="Lexicon", world_scale=(15, 15),
             origin=(0, 0), position=(0.5, -0.5, -2))
        # Make Skills window/button
        self.skills = SkillsWindow(parent=self, model='quad', origin=(-.5, .5),
                                 scale=tab_scale, position=tab_pos,
                                 color=window_fg_color)
        self.skillsbutton = Entity(
            parent=self, model='quad', origin=(-.5, .5),
            position=(0.375, -margin_length, -1), scale=(0.12, button_height),
            color=header_color
        )
        self.skillsbutton.on_click = lambda: self.open_window("open skills")
        Text(parent=self.skillsbutton, text="Skills", world_scale=(15, 15),
             origin=(0, 0), position=(0.5, -0.5, -2))
        # Make Stats window/button
        self.stats = StatsWindow(parent=self, model='quad', origin=(-.5, .5),
                                 scale=tab_scale, position=tab_pos,
                                 color=window_fg_color)
        self.statsbutton = Entity(
            parent=self, model='quad', origin=(-.5, .5),
            position=(0.52, -margin_length, -1), scale=(0.12, button_height),
            color=header_color
        )
        self.statsbutton.on_click = lambda: self.open_window("open stats")
        Text(parent=self.statsbutton, text="Stats", world_scale=(15, 15),
             origin=(0, 0),position=(0.5, -0.5, -2))

        self.input_to_interface = {
            "open items": self.items,
            "open lexicon": self.lex,
            "open skills": self.skills,
            "open stats": self.stats}

        self.input_to_button = {
            "open items": self.itemsbutton,
            "open lexicon": self.lexbutton,
            "open skills": self.skillsbutton,
            "open stats": self.statsbutton
        }

        self.active_tab = self.items
        self.active_button = self.itemsbutton
        self.parent.visible = False

    def input(self, key):
        if key in self.input_to_interface:
            self.open_window(key)

    def open_window(self, key):
        new_active_tab = self.input_to_interface[key]

        new_active_button = self.input_to_button[key]
        if self.active_button != new_active_button:
            new_active_button.color = active_button_color
            self.active_button.color = header_color
            self.active_button.alpha = 155 / 250
            self.active_button = new_active_button

        if new_active_tab == self.active_tab:
            # Close the window
            self.parent.visible = False
            self.active_tab.visible = False
            self.add_colliders()
            self.active_tab = None
        elif not self.parent.visible:
            # Open player window and specified tab, add collider
            self.parent.visible = True
            new_active_tab.visible = True
            self.active_tab = new_active_tab
            self.add_colliders()
        else:
            # Swap to new active tab
            self.active_tab.visible = False
            self.active_tab = new_active_tab
            self.active_tab.visible = True
            # Will likely need to add colliders for lexicon and inventory eventually

    def remove_colliders(self):
        self.parent.collider = None
        self.collider = None
        self.itemsbutton.collider = None
        self.lexbutton.collider = None
        self.skillsbutton.collider = None
        self.statsbutton.collider = None

    def add_colliders(self):
        self.parent.collider = "box"
        self.collider = "box"
        self.itemsbutton.collider = "box"
        self.lexbutton.collider = "box"
        self.skillsbutton.collider = "box"
        self.statsbutton.collider = "box"