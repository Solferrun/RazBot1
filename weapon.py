#!/usr/bin/python
# -*- coding: utf-8 -*-
from random import choice, randint


class Title:
    def __init__(self, name, power):
        self.name = name
        self.power = power


class DamageType:
    def __init__(self, adjective="Actual", noun="Physical", verb="punched"):
        self.adjective = adjective
        self.noun = noun
        self.verb = verb
        self.adjective = adjective


class Weapon:
    def __init__(self, name="BARE HANDS", power=1, damage_type=DamageType()):
        self.power = power
        self.name = name
        self.damage_type = damage_type

    def roll_attack_power(self):
        return randint(self.power*5, self.power*25)


suffixes = [
    Title("of Instant-Death but It's Broken", -3),
    Title("of Apathy", 1),
    Title("of Weakness", 2),
    Title("of Really Serious Burning", 2),
    Title("of Charming", 4),
    Title("of Power", 6),
    Title("of Disarming", 6),
    Title("of Buffing", 6),
    Title("of Slaying", 8),
    Title("of the Apocalypse", 14),
    Title("of Also Healing", 2),
    Title("of Fleeting Power", 30),
    Title("of Stripping", 2),
    Title("of Pleasuring", 3),
    Title("of Tickling", 1),
    Title("of Failing", 4),
    Title("of Winning", 10),
    Title("of Cursing", 8),
    Title("of Why is it Sticky?", 4),
    Title("of Paean", 6),
    Title("of the Shining God", 8),
    Title("of God-Slaying", 1)]

weapon_types = [
    Title("Floppy Fish", 4),
    Title("Shuriken", 8),
    Title("Gauntlet", 8),
    Title("Dirk", 8),
    Title("Rod", 8),
    Title("Quarter-staff", 8),
    Title("Whip", 6),
    Title("Ball and Chain", 8),
    Title("Katana", 12),
    Title("Sword", 10),
    Title("Axe", 10),
    Title("Spear", 10),
    Title("Bow", 8),
    Title("Greatsword", 12),
    Title("Polearm", 12),
    Title("Banana", 3),
    Title("Really Stale Baguette", 4),
    Title("Slingshot", 7),
    Title("Lego Castle", 5),
    Title("Sack of Rocks", 8),
    Title("Laser Rifle", 20)]

damage_types = [
    DamageType("Blazing", "Fire", "burned"),
    DamageType("Freezing", "Ice", "froze"),
    DamageType("Water-Spraying", "Water", "splish-splashed"),
    DamageType("Earthen", "Earth", "crushed"),
    DamageType("Charged", "Air", "zapped"),
    DamageType("Sickly", "Poison", "contaminated"),
    DamageType("Nail-Tipped", "Piercing", "punctured"),
    DamageType("Cursed", "Taint", "tainted"),
    DamageType("Pure", "Holy", "purged"),
    DamageType("Martial", "Physical", "whacked"),
    DamageType("Singing", "Musical", "serenaded"),
    DamageType("Wiggly", "Wiggly Jiggly", "creeped out"),
    DamageType("Imaginary", "KAPOW", "fantasized about attacking"),
    DamageType("Alltrue", "True", "elucidated"),
    DamageType("Healing", "Healing", "healed"),
    DamageType("Shining", "Shiny", "bling-blinged"),
    DamageType("Futuristic", "Temporal", "whomped"),
    DamageType("Pointy", "Pokey", "pricked"),
    DamageType("Foam", "Fun", "bonked"),
    DamageType("Explodey", "Blast", "blew")
    ]


def get_weapon():
    """
    Create and return a random weapon
    """
    damage_type = choice(damage_types)
    wpn_type = choice(weapon_types)
    suffix = choice(suffixes)
    power = wpn_type.power + suffix.power
    name = "{0} {1} {2}".format(damage_type.adjective, wpn_type.name, suffix.name)
    return Weapon(name, power, damage_type)
