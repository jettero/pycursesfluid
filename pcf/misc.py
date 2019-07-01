#!/usr/bin/env python
# coding: utf-8

from itertools import zip_longest
from collections import namedtuple
import re

class PathItem:
    attrlist = ('a', 'b', 'c') # just an example, overload this

    def __init__(self, *args):
        for i,j in zip_longest(self.attrlist, args[:len(self.attrlist)]):
            setattr(self, i, j)

    def __iter__(self):
        for i in self.attrlist:
            v = getattr(self, i)
            if v is None:
                break
            yield v

    def __str__(self):
        return '/' + '/'.join(str(x) for x in self)

    def __repr__(self):
        return f'{self.__class__.__name__}[{str(self)}]'

    @property
    def path(self):
        return str(self)

class HandyMatch:
    pat = g = gd = None

    def __init__(self, pat):
        self.pat = re.compile(pat)

    def __getitem__(self, i):
        if self.gd and i in self.gd:
            return self.gd[i]
        if self.g and 0 < i < len(self.g):
            return self.g[i]

    def __iter__(self):
        yield from self.g

    def as_ntuple(self, *a, **kw):
        x = self.gd.copy()
        x.update(**kw)
        if not a:
            a = sorted(x)
        elif isinstance(a, str):
            a = str.split()
        return namedtuple('HMR', a)(**x)

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
