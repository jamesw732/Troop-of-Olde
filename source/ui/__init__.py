from .bars import BarWindow
from .game_window import GameWindow
from .player_window import PlayerWindow
from .action_bar import ActionBar


class UI:
    def __init__(self):
        self.bars = None
        self.playerwindow = None
        self.gamewindow = None
        self.item_frames = {}

def make_all_ui(ui):
    # pass
    ui.bars = BarWindow()
    ui.playerwindow = PlayerWindow()
    ui.gamewindow = GameWindow()
    ui.actionbar = ActionBar()
