#!/usr/bin/env python
# coding: utf-8

import time
import rtmidi

midiout = rtmidi.MidiOut()
midiout.open_virtual_port("rtmidi example")

# note_on = [0x90, 60, 112] # channel 1, middle C, velocity 112
# note_off = [0x80, 60, 0]
# 0x90: 1001 0000 # note on, channel 1[-1]
# 0x80: 1000 0000 # note off, channel 1[-1]
# 0x60: 1100 0000 # middle C
# 112:  1110 0000 # velocity

for i in range(10):
    note_on = [0x90, 60, 112] # channel 1, middle C, velocity 112
    note_off = [0x80, 60, 0]
    midiout.send_message(note_on)
    time.sleep(0.5)
    midiout.send_message(note_off)

del midiout
