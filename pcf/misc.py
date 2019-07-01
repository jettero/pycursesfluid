#!/usr/bin/env python
# coding: utf-8

from itertools import zip_longest
from collections import namedtuple
import re

class RangySet(set):
    def as_ranges(self, wrap=int):
        r = list()
        l = sorted(self)
        if not l:
            return r

        def wp():
            return wrap(l.pop(0))

        b = e = wp()
        while l:
            if e+1 == l[0]:
                e = wp()
            elif e == b:
                r.append( (b,) )
                b = e = wp()
            else:
                r.append( (b,e) )
                b = e = wp()
        if None not in (b,e):
            if b == e:
                r.append( (b,) )
            else:
                r.append( (b,e) )
        return r

class PathItem:
    attrlist = ('a', 'b', 'c') # just an example, overload this

    def __init__(self, *args):
        for i,j in zip_longest(self.attrlist, args[:len(self.attrlist)]):
            if i.startswith('!'):
                i = i[1:]
            setattr(self, i, j)

    def __iter__(self):
        for i in self.attrlist:
            if i.startswith('!'):
                continue
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

    def __repr__(self):
        return f'{self.__class__.__name__}[{self.pat.pattern}]'

    def check_called(self):
        if None in (self.g, self.gd):
            raise ValueError(f'{self} never called or failed to match on last call')

    def __getitem__(self, i):
        self.check_called()
        if self.gd and i in self.gd:
            return self.gd[i]
        if self.g and 0 < i < len(self.g):
            return self.g[i]

    def __iter__(self):
        self.check_called()
        yield from self.g

    def as_ntuple(self, *a, **kw):
        self.check_called()
        ret = self.gd.copy()
        ret.update(**kw)
        if not a:
            a = sorted(ret)
        return namedtuple('HMR', a)(*[ret.get(i) for i in a])

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
