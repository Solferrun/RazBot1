#!/usr/bin/python
# -*- coding: utf-8 -*-
from time import time
from s3_bucket import load_dict


class Counter:
    def __init__(self, count=0, admins=None):
        self.count = count
        self.admins = admins
        self.last_call = 0
        self.cooldown = 4

    def add(self, amount):
        self.count += amount

    def subtract(self, amount):
        self.count = max(0, self.count - amount)

    def set_to(self, amount):
        now = int(time())
        on_cooldown = self.last_call + self.cooldown > now
        if not on_cooldown:
            self.count = int(min(max(0, amount), 9999999))
            self.last_call = now
            return True
        else:
            return False

    def reset(self):
        self.count = 0

# Populate counters from file
counters = {c['token']: Counter(c['count'], c['admins']) for c in load_dict('counters')}
# Empty dict if counters is None
if not counters:
    counters = {}
