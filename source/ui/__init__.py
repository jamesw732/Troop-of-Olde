from .bars import BarWindow
from .game_window import GameWindow
from .player_window import PlayerWindow


class UI:
    def __init__(self):
        self.bars = None
        self.playerwindow = None
        self.gamewindow = None

def make_all_ui(ui):
    ui.bars = BarWindow()
    ui.playerwindow = PlayerWindow()
    ui.gamewindow = GameWindow()
