from ursina import *

from .base import *

class UIWindow(Entity):
    def __init__(self, header_ratio=0.1, header_text="", bg_alpha=100/255, scale=(0.4, 0.4),
                 position=(0.2, 0.2)):
        # Invisible "canvas" entity
        super().__init__(origin=(-0.5, 0.5), scale=scale, position=position, parent=camera.ui, collider='box',
                         model='quad', alpha=0)
        self.header_ratio = header_ratio
        self.body_ratio = 1 - self.header_ratio

        # The top bar entity
        self.header = Entity(parent=self, origin=(-0.5, 0.5), scale=(1, self.header_ratio),
                             z=-1, color=header_color, model='quad')
        self.header.text = Text(text=header_text, parent=self.header, origin=(0, 0),
                                position=(0.5, -0.5, -1), world_scale=(20, 20))

        # Everything except the header
        self.body = Entity(parent=self, origin=(-0.5, 0.5), scale=(1, self.body_ratio),
                           position=(0, -self.header_ratio, -1), color=window_bg_color, model='quad')

        # Some attrs for dragging logic
        self.step = Vec2(0, 0)
        self.drag_sequence = Sequence(Func(self.move), Wait(1 / 60), loop=True)

        # Hovered/not hovered transparency handling
        self.bg_alpha = bg_alpha
        if self is not mouse.hovered_entity:
            self.unfocus_window()

    def input(self, key):
        if key == "left mouse up":
            self.drag_sequence.finish()

    def on_click(self):
        self.set_step()
        self.drag_sequence.start()

    def set_step(self):
        self.step = self.position - mouse.position

    def move(self):
        if mouse.position:
            max_x = window.right[0] - self.scale_x
            min_x = window.left[0]
            max_y = window.top[1]
            min_y = window.bottom[1] + self.scale_y

            self.position = mouse.position + self.step

            self.x = clamp(self.x, min_x, max_x)
            self.y = clamp(self.y, min_y, max_y)


    def unfocus_window(self):
        set_alpha(self, self.bg_alpha, exclude=[self])

    def focus_window(self):
        set_alpha(self, 1, exclude=[self])

    def on_mouse_enter(self):
        self.focus_window()

    def on_mouse_exit(self):
        self.unfocus_window()

def set_alpha(entity, alpha, exclude=[]):
    if entity not in exclude:
        entity.alpha = alpha
    for child in entity.children:
        set_alpha(child, alpha)
