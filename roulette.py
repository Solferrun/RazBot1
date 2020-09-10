#!/usr/bin/python
# -*- coding: utf-8 -*-
from random import choice


class Roulette:
    def __init__(self, entry_phrase):
        self.entry_phrase = entry_phrase
        self.users = []
            
    def add(self, user):
        """
        Add user to roulette
        """
        if user not in self.users:
            self.users.append(user)
                    
    def result(self):
        """
        End roulette and pick a winner
        """
        if self.users:
            winner = choice(self.users)
            return f"The roulette is over! The winner is {winner}! razCool"
        else:
            return "No one entered, and no one won! razHands"
    

round_obj = None
