#!/usr/bin/env python
# coding: utf-8

import time
import rtmidi
import logging

log = logging.getLogger('pcf.metronome')

from pcf.beatclock import BeatClock

class Metronome:
    def __init__(self, *notes, channel=1, beats_per_minute=120):
        ''' channel and beats_per_minute are hopefully self explanatory
            notes is a list of notes to play … by number … 60 being middle-c
            notes can also be tuples themselves … second value is velocity, eg
            all c, but different velocities

            m = Metronome( (60,120), (60,90), (60,90) ) # nice little waltz

        '''
        if not (0 <= channel <= 15):
            channel = 1
        self.channel = channel

        if not notes:
            notes = (60,)
        self.notes = notes
        self.npos = 0

        self.beat_duration = (0.95 / beats_per_minute)

        self.beatclock = BeatClock(callback=self.fire, beats_per_minute=beats_per_minute)
        self.midiout = rtmidi.MidiOut()
        self.midiout.open_virtual_port("pcf.metronome")

        if not (0 < self.beat_duration < 1):
            self.beat_duration = 0.1

        self.condition = False

    def start(self):
        self.condition = True
        self.beatclock.start()

    def stop(self):
        self.condition = False
        self.beatclock.stop()

    def fire(self):
        # the debug logging feels useful for debugging, but the logging methods
        # use threading locks and don't plan ahead for this sort of signal
        # based scheduling; so leave logging commented out unless there's a
        # need for it.

        note = self.notes[self.npos]
        vel = 112

        if isinstance(note, (list,tuple)):
            note,vel = note

        self.npos = (self.npos + 1) % len(self.notes)

        self.midiout.send_message([0x90 + self.channel, note, vel])
        time.sleep(self.beat_duration)
        self.midiout.send_message([0x80 + self.channel, note, 0])

        return self.condition
