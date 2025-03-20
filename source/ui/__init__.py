from .base import ui
from .bars import BarWindow
from .game_window import GameWindow
from .player_window import PlayerWindow


def make_all_ui():
    ui.bars = BarWindow()
    ui.playerwindow = PlayerWindow()
    ui.gamewindow = GameWindow()
