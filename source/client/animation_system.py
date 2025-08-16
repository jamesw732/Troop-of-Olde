from ursina import *

from .animator import CharacterAnimator


class AnimationSystem(Entity):
    """Handles by-frame animation updates and CharacterAnimator creation

    Provides a wrapper interface into CharacterAnimator"""
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

    def start_run_cycle(self, char):
        anim = self.uuid_to_anim[char.uuid]
        anim.start_run_cycle()

    def end_run_cycle(self, char):
        anim = self.uuid_to_anim[char.uuid]
        anim.end_run_cycle()

    def char_enter_combat(self, char):
        anim = self.uuid_to_anim[char.uuid]
        anim.enter_combat()

    def char_exit_combat(self, char):
        anim = self.uuid_to_anim[char.uuid]
        anim.exit_combat()

    def do_attack(self, char, slot):
        anim = self.uuid_to_anim[char.uuid]
        anim.do_attack(slot)

    def set_equipment_slot(self, char, slot, item):
        anim = self.uuid_to_anim[char.uuid]
        anim.set_equipment_slot(slot, item)
