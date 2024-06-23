from ursina import *

class DraggableHeader(Entity):
    def __init__(self, position=Vec2(0, 0), scale=(.5, 0.03), color=color.yellow):
        super().__init__(parent=camera.ui, model='quad', origin=(-.5, .5),
                         collider='box', position=position, scale=scale,
                         color=color)
        self.dragging = False
        self.step = Vec2(0, 0)

        self.max_x = window.right[0] - self.scale_x
        self.min_x = window.left[0]
        self.max_y = window.top[1]
        self.min_y = window.bottom[1] + self.scale_y

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
                self.x = clamp(self.x, self.min_x, self.max_x)
                self.y = clamp(self.y, self.min_y, self.max_y)
