#!/usr/bin/python
# -*- coding: utf-8 -*-


def join_room(s):
    """Enter Twitch IRC chat"""
    readbuffer = ""
    loading = True
    while loading:
        try:
            r = s.recv(1024)
            readbuffer = readbuffer + r.decode('UTF-8')
            temp = readbuffer.split("\n")
            readbuffer = temp.pop()
            for line in temp:
                print(f">> {line}")
                loading = is_loading(line)
        except BlockingIOError:
            return False
    return True


def is_loading(line):
    """IRC Loading check"""
    return "End of /NAMES list" not in line and f'ROOMSTATE' not in line
