#!/usr/bin/env python
# -*- coding: utf-8 -*-


class Battle(object):
    """docstring for Battle"""
    def __init__(self, dragon, ppl):
        super(Battle, self).__init__()
        self.dragon = dragon
        self.ppl = ppl
        self.started = False
        self.finish = False
        