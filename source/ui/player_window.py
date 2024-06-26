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
            text=self.player.cname
        )
        # Make outer window
        super().__init__(
            parent=header, model='quad', origin=(-.5, .5),
            position=(0, -1), scale=(1, 12),
            color=window_bg_color,
            collider='box'
        )
        # Make Items window/button
        self.items = ItemsWindow(parent=self, model='quad', origin=(-.5, .5),
                                 scale=(.95, .8725), position=(.025, -.1, -1),
                                 color=window_fg_color)
        self.itemsbutton = Entity(
            parent=self, model='quad', origin=(-.5, .5),
            position=(0.025, -0.01, -1), scale=(0.12, 0.08),
            color=header_color, collider="box"
        )
        self.itemsbutton.on_click = lambda: self.open_window("open items")
        Text(parent=self.itemsbutton, text="Items", world_scale=(15, 15),
             origin=(0, 0), position=(0.5, -0.5, -2))
        # Make Lexicon window/button
        self.lex = LexiconWindow(parent=self, model='quad', origin=(-.5, .5),
                                 scale=(.95, .8725), position=(.025, -.1, -1),
                                 color=window_fg_color)
        self.lexbutton = Entity(
            parent=self, model='quad', origin=(-.5, .5),
            position=(0.17, -0.01, -1), scale=(0.16, 0.08),
            color=header_color
        )
        self.lexbutton.on_click = lambda: self.open_window("open lexicon")
        Text(parent=self.lexbutton, text="Lexicon", world_scale=(15, 15),
             origin=(0, 0), position=(0.5, -0.5, -2))
        # Make Skills window/button
        self.skills = SkillsWindow(parent=self, model='quad', origin=(-.5, .5),
                                 scale=(.95, .8725), position=(.025, -.1, -1),
                                 color=window_fg_color)
        self.skillsbutton = Entity(
            parent=self, model='quad', origin=(-.5, .5),
            position=(0.355, -0.01, -1), scale=(0.12, 0.08),
            color=header_color
        )
        self.skillsbutton.on_click = lambda: self.open_window("open skills")
        Text(parent=self.skillsbutton, text="Skills", world_scale=(15, 15),
             origin=(0, 0), position=(0.5, -0.5, -2))
        # Make Stats window/button
        self.stats = StatsWindow(parent=self, model='quad', origin=(-.5, .5),
                                 scale=(.95, .8725), position=(.025, -.1, -1),
                                 color=window_fg_color)
        self.statsbutton = Entity(
            parent=self, model='quad', origin=(-.5, .5),
            position=(0.5, -0.01, -1), scale=(0.12, 0.08),
            color=header_color
        )
        self.statsbutton.on_click = lambda: self.open_window("open stats")
        Text(parent=self.statsbutton, text="Stats", world_scale=(15, 15),
             origin=(0, 0),position=(0.5, -0.5, -2))

        self.input_triggers = {
            "open items": self.items,
            "open lexicon": self.lex,
            "open skills": self.skills,
            "open stats": self.stats}

        self.active_tab = self.items
        self.parent.visible = False

    def input(self, key):
        if key in self.input_triggers:
            self.open_window(key)

    def open_window(self, key):
        new_active_tab = self.input_triggers[key]
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