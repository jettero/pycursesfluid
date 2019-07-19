#!/usr/bin/env python
# coding: utf-8

import time
import signal
import logging

log = logging.getLogger(__name__)

class BeatClock:
    def __init__(self, bpm, callback=None):
        self.cb = callback
        self.bpm = bpm
        self.started = False

    @property
    def spb(self):
        return 1.0 / (self.bpm / 60.0)

    def __repr__(self):
        return f'BC({self.bpm} bpm)'

    def __enter__(self):
        spb = self.spb
        signal.signal(signal.SIGALRM, self.fire_timer)
        signal.setitimer(signal.ITIMER_REAL, spb, spb)
        self.started = time.time()
        return self

    def __exit__(self, e_type, e_obj, e_tb):
        if not isinstance(e_obj, BeatClock):
            log.debug("%s exited with-block normally", repr(self))
        else:
            log.debug("%s exited with-block via exception", repr(self))
