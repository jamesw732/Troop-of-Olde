from ursina import *

from . import *

class Header(Entity):
    """Class for draggable headers. Any interface that uses a Header
    should designate it as the parent."""
    def __init__(self, position=Vec2(0, 0), scale=Vec2(.5, 0.03),
                 color=header_color, text="", ignore_key=lambda c: False):
        """
        window_size: scale of the whole window relative to camera.ui, used for determining if mouse is hovering the parented window
        ignore_key: function to tell the header which children to ignore when setting
        transparency, usually ignore text"""
        super().__init__(parent=camera.ui, model='quad', origin=(-.5, .5),
                         collider='box', position=position, scale=scale,
                         color=color)
        self.dragging = False
        self.step = Vec2(0, 0)

        self.text = Text(text=text, parent=self, origin=(0, 0),
                         position=(0.5, -0.5, -1), world_scale=(20, 20))

        self.ignore_key = ignore_key

        self.transparent = False

        self.ui_scale = self.getScale(camera.ui)

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
        hovered = self.get_hovered()
        if self.transparent and hovered:
            set_transparency(self, 1)
            self.transparent = False
        elif not self.transparent and not hovered:
            set_transparency(self, 150 / 255, ignore_key=self.ignore_key)
            self.transparent = True

    def set_step(self):
        self.step = self.position - mouse.position

    def set_ui_scale(self, child):
        """Set the scale with respect to camera.ui"""
        self.ui_scale = self.getScale(camera.ui) + Vec3(0, child.getScale(camera.ui)[1], 0)

    def get_hovered(self):
        """Return whether the mouse hovers the parented window"""
        left = self.getX(camera.ui)
        top = self.getY(camera.ui)
        right = left + self.ui_scale[0]
        bottom = top - self.ui_scale[1]
        return (left <= mouse.x <= right) and (bottom <= mouse.y <= top)