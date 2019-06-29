#!/usr/bin/env python3
# coding: UTF-8

import sys, re
import subprocess
import fnmatch
import argparse

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

class GraphItem:
    def __init__(self, layer, name):
        self.layer = layer
        self.name = name
        self.properties = set()
        self.connected = set()

    @property
    def id(self):
        return f'{self.layer}:{self.name}'

    def __str__(self):
        ret = f'{self.id}'
        if self.properties:
            ret += f'{self.properties}'
        for c in self.connected:
            ret += f' →{c}'
        return ret

class JackGraphStatus:
    JHM = HandyMatch(r'^(?P<indent>\s*)(?P<layer>[^:]+):(?P<name>.+)')

    def __init__(self):
        self.items = list()
        self.slurp()

    def slurp(self):
        p = subprocess.Popen(['jack_lsp', '-pc'], stdout=subprocess.PIPE)
        out,err = p.communicate()
        for line in out.splitlines():
            if self.JHM(line):
                if self.JHM['indent']:
                    if self.JHM['layer'] == 'properties':
                        self.items[-1].properties.update( self.JHM['name'].strip(' ,').split(',') )
                    else:
                        self.items[-1].connected.add( ':'.join([self.JHM['layer'], self.JHM['name']]) )
                else:
                    item = GraphItem(self.JHM['layer'], self.JHM['name'])
                    print(f'found {item}')
                    self.items.append(item)

    def pick(self, name, *properties, layer=None):
        for item in self.items:
            if layer is not None:
                if item.layer != layer:
                    continue
            for p in properties:
                if p not in item.properties:
                    continue
            if '*' not in name:
                name = f'*{name}*'
            if fnmatch.fnmatch(item.id.lower(), name.lower()):
                print(f'picked {item}')
                return item
        if properties:
            print(f'{name} failed to match anything with properties: {properties}')
        else:
            print(f'{name} failed to match anything')

    def connect(self, iname, oname):
        iobj = self.pick(iname, 'output', 'physical')
        if iobj:
            oobj = self.pick(oname, 'input', layer=iobj.layer)
        else:
            oobj = False

        if iobj and oobj:
            if iobj.id in oobj.connected:
                print("already connected")
            else:
                p = subprocess.Popen(['jack_connect', iobj.id, oobj.id])
                p.communicate()
                p = subprocess.Popen(['jack_lsp', '-c'], stdout=subprocess.PIPE)
                out,err = p.communicate()
                print(out.decode(), end='')

def connect(in_glob, out_glob):
    status = JackGraphStatus()
    status.connect(in_glob, out_glob)
    return 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("in_glob", type=str)
    parser.add_argument("out_glob", type=str)
    args = parser.parse_args()
    sys.exit( connect(args.in_glob, args.out_glob) )
