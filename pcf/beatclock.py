#!/usr/bin/env python
# coding: utf-8

import time
import signal
import logging

log = logging.getLogger(__name__)

class BeatClock:
    def __init__(self, callback=None, beats_per_minute=60):
        self.cb = callback
        self.beats_per_minute = beats_per_minute
        self.started = False

    def fire_timer(self, signum, frame):
        if callable(self.cb):
            if self.cb():
                return
        self.stop()

    @property
    def seconds_per_beat(self):
        bps = self.beats_per_minute / 60.0
        return 1.0 / bps

    def __repr__(self):
        return f'BC({self.beats_per_minute} bpm; {self.seconds_per_beat:0.04f} spb)'

    def start(self):
        seconds_per_beat = self.seconds_per_beat
        signal.signal(signal.SIGALRM, self.fire_timer)
        signal.setitimer(signal.ITIMER_REAL, seconds_per_beat, seconds_per_beat)
        self.started = time.time()

    def stop(self):
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
        signal.setitimer(signal.ITIMER_REAL, 0)
