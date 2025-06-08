from ursina import Vec3

from ..base import all_skills, default_equipment, default_phys_attrs, default_cb_attrs

state_defs = {
    # Used for ground-up Character creation, stored by client and sent to server
    "base_combat": { 
        "statichealth": int,
        "staticenergy": int,
        "staticarmor": int,

        "str": int,
        "dex": int,
        "ref": int,

        "haste": int,
        "speed": int,
    },
    # Used to update Player Character's stats, sent by server
    "pc_combat": {
        "health": int,
        "maxhealth": int,
        "statichealth": int,
        "energy": int,
        "maxenergy": int,
        "staticenergy": int,
        "armor": int,
        "maxarmor": int,
        "staticarmor": int,

        "str": int,
        "dex": int,
        "ref": int,

        "haste": int,
        "speed": int,
    },
    # Used to update NPC's stats, sent by server to client to represent non-player-characters
    "npc_combat": {
        "health": int,
        "maxhealth": int,
    },
    "item_stats":{
        "statichealth": int,
        "staticenergy": int,
        "staticarmor": int,
        "str": int,
        "dex": int,
        "ref": int,
        "haste": int,
        "speed": int
    },
    # Used to update character's physical state, sent to/by server
    "physical": {
        "model": str,
        "scale": Vec3,
        "position": Vec3,
        "rotation": Vec3,
        "color": str,
        "cname": str
    },
    # Used to initialize skills. Skill level ups are done individually, not with a state.
    "skills": {skill: int for skill in all_skills},
}


# where to look for defaults if not found in state source
statetype_to_defaults = {
    "base_combat": default_cb_attrs,
    "pc_combat": default_cb_attrs,
    "npc_combat": default_cb_attrs,
    "physical": default_phys_attrs,
    "item_stats": {stat: 0 for stat in state_defs["item_stats"]}
}

type_to_default = {
    int: 0,
    float: 0.0,
    Vec3: Vec3(0, 0, 0),
    str: ""
}
