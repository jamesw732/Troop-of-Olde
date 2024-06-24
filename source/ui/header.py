from ursina import *

from .base import *

class Header(Entity):
    """Class for draggable headers. Any interface that uses a Header
    should designate it as the parent."""
    def __init__(self, position=Vec2(0, 0), scale=Vec2(.5, 0.03),
                 color=color.yellow, text=""):
        super().__init__(parent=camera.ui, model='quad', origin=(-.5, .5),
                         collider='box', position=position, scale=scale,
                         color=color)
        self.dragging = False
        self.step = Vec2(0, 0)

        self.text = Text(text=text, parent=self, origin=(0, 0),
                         position=(0.5, -0.5, -1), world_scale=(20, 20))

        self.transparent = False

    def input(self, key):
        if self.hovered and key == "left mouse down":
            self.dragging = True
            self.step = self.position - mouse.position
        elif self.dragging and key == "left mouse up":
            self.dragging = False

    def update(self):
        if self.dragging:
            if mouse.position:
                self.position = mouse.position + self.step

                max_x = window.right[0] - self.scale_x
                min_x = window.left[0]
                max_y = window.top[1]
                min_y = window.bottom[1] + self.scale_y
                self.x = clamp(self.x, min_x, max_x)
                self.y = clamp(self.y, min_y, max_y)
        hovered = get_hovered(self)
        if self.transparent and hovered:
            set_transparency(self, 1, ignore_text=True)
            self.transparent = False
        elif not self.transparent and not hovered:
            set_transparency(self, 155 / 250)
            self.transparent = True