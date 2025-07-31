"""Represents the physical player/npc entities in game, unified for both
the server and client.
The functionality of Characters on the client and server is very different,
(and also player characters vs NPCs), but these distinctions are delegated
to the respective controllers in controllers.py.
"""
import os

from ursina import *
from ursina.mesh_importer import imported_meshes
from direct.actor.Actor import Actor
from panda3d.core import NodePath

from .base import *
from .combat import get_wpn_range
from .states import *

class Character(Entity):
    def __init__(self):
        """Base Character class representing the intersection of server and client-side Characters.

        Populates default values for everything.
        """
        super().__init__()
        for attr, val in default_char_attrs.items():
            setattr(self, attr, copy(val))
        for attr, val in init_char_attrs.items():
            setattr(self, attr, copy(val))

    def update_max_ratings(self):
        """Adjust max ratings, for example after receiving a stat update."""
        self.maxhealth = self.statichealth
        self.maxenergy = self.staticenergy
        self.health = min(self.maxhealth, self.health)
        self.energy = min(self.maxenergy, self.energy)

    def increase_health(self, amt):
        """Function to be used whenever increasing character's health"""
        self.health = min(self.maxhealth, self.health + amt)

    def reduce_health(self, amt):
        """Function to be used whenever decreasing character's health"""
        self.health -= amt

    def start_jump(self):
        """Do the things required to make the character jump"""
        if self.grounded:
            self.jumping = True
            self.grounded = False

    def cancel_jump(self):
        """Reset self.jumping, remaining jump height"""
        self.jumping = False
        self.rem_jump_height = self.max_jump_height

    def set_target(self, target):
        if self.target is not target:
            target.targeted_by.append(self)
        self.target = target

    def get_tgt_los(self, target):
        """Returns whether the target is in line of sight"""
        sdist = sqdist(self.position, self.target.position)
        src_pos = self.position + Vec3(0, 0.8 * self.scale_y, 0)
        tgt_pos = target.position + Vec3(0, 0.8 * target.scale_y, 0)
        dir = tgt_pos - src_pos
        line_of_sight = raycast(src_pos, direction=dir, distance=inf,
                                ignore=[entity for entity in scene.entities if isinstance(entity, Character)])
        if line_of_sight.hit:
            entity = line_of_sight.entity
            if sqdist(entity.position, self.position) < sdist:
                return False
        return True

    def tick_gcd(self):
        """Ticks up the global cooldown for powers"""
        self.gcd_timer = min(self.gcd_timer + time.dt, self.gcd)

    def get_on_gcd(self):
        """Returns whether the character is currently on the global cooldown for powers"""
        return self.gcd_timer < self.gcd

    def find_auto_equip_slot(self, item):
        """Finds the equipment slot to auto equip item to"""
        exclude_slots = set()
        for slot in item.info["equip_slots"]:
            cur_item = self.equipment[slot]
            if cur_item is None and slot not in exclude_slots:
                return slot
            elif cur_item is not None:
                exclude_slots |= set(cur_item.info["equip_exclude_slots"])
        return item.info["equip_slots"][0]

    def find_auto_inventory_slot(self):
        """Finds the inventory slot to auto place item to"""
        try:
            return next((s for s, item in enumerate(self.inventory) if item is None))
        except StopIteration:
            return -1

    def container_swap_locs(self, to_container, to_slot, from_container, from_slot):
        """Swap two indices of containers (possibly same or different) if possible.

        Handles specific-container logic such as equipping 2-handed weapons also removing
        offhand."""
        item1 = from_container[from_slot]
        if item1 is None:
            # Should be safe to assume otherwise, but just in case
            return
        item2 = to_container[to_slot]
        initial_swaps = [(item1, to_container, to_slot, from_container, from_slot),
                         (item2, from_container, from_slot, to_container, to_slot)]
        # Dict mapping tgt container name to src container name to (item, tgt slot, src slot)
        # Essentially a table of tgt container by src container
        move_dict = dict()
        def move_dict_insert(item, tgt_container, tgt_slot, src_container, src_slot):
            """Takes a move in flat structure and puts it in move_dict"""
            if tgt_container.name not in move_dict:
                move_dict[tgt_container.name] = {}
            if src_container.name not in move_dict[tgt_container.name]:
                move_dict[tgt_container.name][src_container.name] = []
            move_dict[tgt_container.name][src_container.name].append((item, tgt_slot, src_slot))
        for item, tgt_container, tgt_slot, src_container, src_slot in initial_swaps:
            move_dict_insert(item, tgt_container, tgt_slot, src_container, src_slot)
        # Compute all consequences of moving item to equipment, particularly for 2h
        if "equipment" in move_dict:
            if "inventory" in move_dict["equipment"]:
                moves = move_dict["equipment"]["inventory"]
                for item, tgt_slot, src_slot in list(moves):
                    if item is None:
                        continue
                    # Unequip items equipped to slots used by this item
                    for exclude_slot in item.info["equip_exclude_slots"]:
                        item_to_move = self.equipment[exclude_slot]
                        if item_to_move is None:
                            continue
                        empty_inv_slot = self.find_auto_inventory_slot()
                        if empty_inv_slot < 0:
                            return
                        move_dict_insert(item_to_move, self.inventory, empty_inv_slot,
                                         self.equipment, exclude_slot)
                        move_dict_insert(None, self.equipment, exclude_slot,
                                         self.inventory, empty_inv_slot)
                    # Unequip items equipped to another slot that need tgt_slot
                    for slot, multislot_item in enumerate(self.equipment):
                        if multislot_item is None:
                            continue
                        for exclude_slot in multislot_item.info["equip_exclude_slots"]:
                            if exclude_slot == tgt_slot:
                                move_dict_insert(multislot_item, self.inventory, src_slot,
                                                 self.equipment, slot)
                                move_dict_insert(None, self.equipment, slot,
                                                 self.inventory, src_slot)
        # Validate equipment moves
        for src_container, moves in move_dict.get("equipment", {}).items():
            for item, tgt_slot, src_slot in moves:
                if item is None:
                    continue
                if tgt_slot not in item.info["equip_slots"]:
                    return
        # Perform all moves, case by case
        for item, tgt_slot, src_slot in move_dict.get("equipment", {}).get("inventory", {}):
            self.equipment[tgt_slot] = item
            if item is not None:
                item.leftclick = "unequip"
                item.stats.apply_diff(self)
        for item, tgt_slot, src_slot in move_dict.get("equipment", {}).get("equipment", {}):
            self.equipment[tgt_slot] = item
        for item, tgt_slot, src_slot in move_dict.get("inventory", {}).get("equipment", {}):
            self.inventory[tgt_slot] = item
            if item is not None:
                item.leftclick = "equip" # This may need some better logic some day
                item.stats.apply_diff(self, remove=True)
        for item, tgt_slot, src_slot in move_dict.get("inventory", {}).get("inventory", {}):
            self.inventory[tgt_slot] = item
        self.update_max_ratings()

    @property
    def model_name(self):
        """Getter for model_name property, used for interoperability with
        the Panda3D Actor ClientCharacter.model_child"""
        return self._model_name

    @model_name.setter
    def model_name(self, new_model):
        """Setter for model_name property, used for interoperability
        with the Panda3D Actor ClientCharacter.model_child

        new_model: name of model file (no other path information)"""
        self._model_name = new_model

    @property
    def model_color(self):
        """Getter for model_color property, used for interoperability
        with the Panda3D Actor ClientCharacter.model_child"""
        return self._model_color

    @model_color.setter
    def model_color(self, new_color):
        """Setter for model_color property, used for interoperability
        with the Panda3D Actor ClientCharacter.model_child

        new_color: name of model file (no other path information)"""
        if isinstance(new_color, str):
            new_color = color.colors[new_color]
        self._model_color = new_color

    @property
    def equipment_id(self):
        if not self.equipment:
            return -1
        return self.equipment.inst_id

    @property
    def equipment_inst_ids(self):
        if not self.equipment:
            return [-1] * num_equipment_slots
        return [item.inst_id if item else -1 for item in self.equipment]

    @property
    def inventory_id(self):
        if not self.inventory:
            return -1
        return self.inventory.inst_id

    @property
    def inventory_inst_ids(self):
        if not self.inventory:
            return [-1] * num_inventory_slots
        return [item.inst_id if item else -1 for item in self.inventory]

    @property
    def powers_inst_ids(self):
        if not self.powers:
            return [-1] * default_num_powers
        return [power.inst_id if power else -1 for power in self.powers]