#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random


class Dragon(object):

    def __init__ (self, name, attack=19, health=1000):
        self.name = name
        self.health = health
        self.attack = attack

    def check_dragon_attack(self, dragon_atk_chance):
        if dragon_atk_chance >= random.random():
            return True
        return False

    def check_dragon_skill(self):
        pass

    def check_dragon_fury(self):
        pass