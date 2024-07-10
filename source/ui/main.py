from ursina import *

from .base import ui
from .bars import BarWindow
from .player_window import PlayerWindow
from .game_window import GameWindow


def make_all_ui():
    ui.bars = BarWindow()
    ui.playerwindow = PlayerWindow()
    ui.gamewindow = GameWindow()
