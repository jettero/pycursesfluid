#!/usr/bin/env python
# coding: utf-8

import re

class HandyMatch:
    def __init__(self, pat):
        self.pat = re.compile(pat)
        self.g = self.gd = None
    def __getitem__(self, i):
        if self.gd and i in self.gd:
            return self.gd[i]
        if self.g and 0 < i < len(self.g):
            return self.g[i]
    def __call__(self, line):
        if isinstance(line, (bytes,bytearray)):
            line = line.decode()
        m = self.pat.match(line)
        if m:
            self.g = m.groups()
            self.gd = m.groupdict()
            return True
        self.g = self.gd = None
        return False
