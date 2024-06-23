from ursina import *

class Header(Entity):
    """Class for draggable headers. Any interface that uses a Header
    should designate it as the parent."""
    def __init__(self, position=Vec2(0, 0), scale=(.5, 0.03), color=color.yellow):
        super().__init__(parent=camera.ui, model='quad', origin=(-.5, .5),
                         collider='box', position=position, scale=scale,
                         color=color)
        self.dragging = False
        self.step = Vec2(0, 0)

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
