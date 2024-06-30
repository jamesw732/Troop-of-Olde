from ursina import *
from .bars import BarWindow
from .player_window import PlayerWindow
from .game_window import GameWindow

class UI:
    def __init__(self):
        self.bars = None
        self.playerwindow = None
        self.gamewindow = None
    
    def make(self):
        self.bars = BarWindow()
        self.playerwindow = PlayerWindow()
        self.gamewindow = GameWindow()

ui = UI()