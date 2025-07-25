from .bars import BarWindow
from .game_window import GameWindow
from .player_window import PlayerWindow
from .action_bar import ActionBar


class UI:
    def __init__(self):
        self.bars = None
        self.playerwindow = None
        self.gamewindow = None
        self.actionbar = None
        self.item_frames = {}

    def make_all_ui(self, char, ctrl):
        self.bars = BarWindow(char)
        self.playerwindow = PlayerWindow(char)
        self.gamewindow = GameWindow()
        self.actionbar = ActionBar(char, ctrl)

        # Should probably not do this post-hoc, pull parts of PlayerWindow.__init__
        # into functions and call them here
        items_window = self.playerwindow.items
        equipment = items_window.equipment_frame
        inventory = items_window.inventory_frame
        self.item_frames[equipment.container.container_id] = equipment
        self.item_frames[inventory.container.container_id] = inventory

ui = UI()
