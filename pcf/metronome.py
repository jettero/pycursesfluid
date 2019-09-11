#!/usr/bin/env python
# coding: utf-8

import time
import rtmidi
import logging

log = logging.getLogger('pcf.metronome')

from pcf.beatclock import BeatClock

class Note:
    def __init__(self, note=60, velocity=112, channel=1):
        self.note     = max(0, min(127, note))
        self.velocity = max(0, min(127, velocity))
        self.channel  = max(0, min(15, channel))

        self.on  = [0x90 + self.channel, self.note, self.velocity]
        self.off = [0x80 + self.channel, self.note, self.velocity]

class Metronome:
    def __init__(self, *notes, channel=1, beats_per_minute=120):
        ''' channel and beats_per_minute are hopefully self explanatory
            notes is a list of notes to play … by number … 60 being middle-c
            notes can also be tuples themselves … second value is velocity, eg
            all c, but different velocities

            m = Metronome( (60,120), (60,90), (60,90) ) # nice little waltz

        '''
        self.channel = channel

        if not notes:
            notes = (60,)
        self.notes = list()
        self.npos = 0
        for n in notes:
            if isinstance(n, Note):
                self.notes.append(n)
            elif isinstance(n, (list,tuple)):
                self.notes.append(Note(*n))
            else:
                self.notes.append(Note(n))

        self.beatclock = BeatClock(callback=self.fire, beats_per_minute=beats_per_minute)
        self.beats_per_minute = beats_per_minute
        self.midiout = rtmidi.MidiOut()
        self.midiout.open_virtual_port("pcf.metronome")
        self.condition = False

    @property
    def beats_per_minute(self):
        return self.beatclock.beats_per_minute

    @beats_per_minute.setter
    def beats_per_minute(self, v):
        self.beat_duration = (0.95 / v)
        if self.beat_duration < 0.1:
            self.beat_duration = 0.1
        elif self.beat_duration > 0.9:
            self.beat_duration = 0.9
        self.beatclock.beats_per_minute = v

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
        self.npos = (self.npos + 1) % len(self.notes)

        self.midiout.send_message(note.on)
        time.sleep(self.beat_duration)
        self.midiout.send_message(note.off)

        return self.condition
