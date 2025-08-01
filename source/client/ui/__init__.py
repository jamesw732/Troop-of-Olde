from .action_bar import ActionBar
from .bars import BarWindow
from .game_window import GameWindow
from .items_manager import ItemsManager
from .player_window import PlayerWindow


class UI:
    def __init__(self):
        self.bars = None
        self.playerwindow = None
        self.gamewindow = None
        self.actionbar = None
        self.items_manager = None

    def make_all_ui(self, char, ctrl):
        self.items_manager = ItemsManager(char)
        self.bars = BarWindow(char)
        self.playerwindow = PlayerWindow(char, self.items_manager)
        self.gamewindow = GameWindow()
        self.actionbar = ActionBar(char, ctrl)


ui = UI()
