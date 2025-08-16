from ursina import *

from .animator import CharacterAnimator


class AnimationSystem(Entity):
    """Handles by-frame animation updates and CharacterAnimator creation"""
    def __init__(self, global_containers):
        super().__init__()
        self.uuid_to_anim = global_containers.uuid_to_anim

    def make_animator(self, character):
        animator = CharacterAnimator(character.model_child, equipment=character.equipment)
        self.uuid_to_anim[character.uuid] = animator
        return animator

    def update(self):
        for anim in self.uuid_to_anim.values():
            anim.update_animation_weights()
