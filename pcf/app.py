#!/usr/bin/env python
# coding: utf-8

import urwid
import time
from pcf.fluidsynth import FluidSynth
from pcf.misc import PathItem

FluidSynthObj = None
def get_fso():
    global FluidSynthObj
    if FluidSynthObj is None:
        FluidSynthObj = FluidSynth()
    return FluidSynthObj

InstTree_t = InstTree = None
def get_tree(*k, cache_timeout=1):
    global InstTree_t, InstTree
    now = time.time()
    if InstTree is None or (now - InstTree_t) >= cache_timeout:
        InstTree = dict()
        InstTree['/'] = top = FluidNode('FluidSynth')
        fso = get_fso()
        for font,name,path in fso.fonts:
            n = FluidNode(path, font, parent=top)
            InstTree[n.path] = n
        for name,font,bank,prog in fso.instruments:
            fp = f'/{font}'
            bp = fp + f'/{bank}'
            if bp not in InstTree:
                InstTree[bp] = FluidNode(f'Bank-{bank}', font,bank, parent=InstTree[fp])
            n = FluidNode(name, font,bank,prog, parent=InstTree[bp])
            InstTree[n.path] = n
        InstTree_t = now
    if k:
        return tuple( InstTree.get(x) for x in k )
    return InstTree

class FluidWidget(urwid.TreeWidget):
    pass

class FluidNode(urwid.ParentNode, PathItem):
    attrlist = ('name', 'font', 'bank', 'prog')

    def __init__(self, name='FluidSynth', font=None, bank=None, prog=None, parent=None):
        PathItem.__init__(self, font, bank, prog)
        urwid.ParentNode.__init__(self, name, key=self.path, parent=parent)
        self.kids = list()

    def load_child_keys(self):
        return tuple( k for k,v in get_tree().items() if str(v.get_parent()) == str(self) )

    def load_child_node(self, key):
        return get_tree(key)[0]

    def load_widget(self):
        return FluidWidget(self)

    def get_key(self):
        return self.path

class PCFApp:
    palette = [ ('body', 'light gray', 'default'),
                ('head', 'yellow', 'dark blue'),
                ('foot', 'white', 'dark blue'),
            ]

    def __init__(self):
        self.header = urwid.Text('header')
        self.footer = urwid.Text('footer')
        self.listbox = urwid.TreeListBox(urwid.TreeWalker(FluidNode()))
        self.view = urwid.Frame(
            urwid.AttrWrap(self.listbox, 'body'),
            header=urwid.AttrWrap(self.header, 'head'),
            footer=urwid.AttrWrap(self.footer, 'foot'))

    def main(self):
        self.loop = urwid.MainLoop(self.view, self.palette, unhandled_input=self.unhandled_input)
        self.loop.run()

    def unhandled_input(self, k):
        if k in ('q', 'Q'):
            raise urwid.ExitMainLoop()
