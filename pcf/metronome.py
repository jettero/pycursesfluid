#!/usr/bin/env python
# coding: utf-8

import time
import rtmidi
import logging

log = logging.getLogger('pcf.metronome')

from pcf.beatclock import BeatClock

class Metronome:
    def __init__(self, channel=2, beats_per_minute=60, *notes):
        ''' channel and beats_per_minute are hopefully self explanatory
            notes is a list of notes to play … by number … 60 being middle-c
        '''
        self.channel = channel-1
        if self.channel < 0:
            self.channel = 0

        if not notes:
            notes = (60,)
        self.notes = notes
        self.npos = 0

        self.beat_duration = 0.9 * (1.0 / beats_per_minute)
        self.beatclock = BeatClock(callback=self.fire, beats_per_minute=beats_per_minute)
        self.midiout = rtmidi.MidiOut()
        self.midiout.open_virtual_port("pcf.metronome")

        if not (0 < self.beat_duration < 1):
            self.beat_duration = 0.1

    def start(self):
        self.beatclock.start()

    def fire(self):
        # the debug logging feels useful for debugging, but the logging methods
        # use threading locks and don't plan ahead for this sort of signal
        # based scheduling; so leave logging commented out unless there's a
        # need for it.

        note = self.notes[self.npos]
      # log.debug('pcf.metronome.fire() [on]')
        self.midiout.send_message([0x90 + self.channel, note, 112])
        time.sleep(self.beat_duration)
      # log.debug('pcf.metronome.fire() [off]')
        self.midiout.send_message([0x80 + self.channel, note, 112])

        return True
