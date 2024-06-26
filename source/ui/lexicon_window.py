from ursina import *

from .base import *
from .header import *
from ..gamestate import gs

class LexiconWindow(Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)