#!/usr/bin/env python
# coding: utf-8

import urwid
from pcf.fluidsynth import FluidSynth
from pcf.misc import PathItem

FluidSynthObj = None
def get_fso():
    global FluidSynthObj
    if FluidSynthObj is None:
        FluidSynthObj = FluidSynth()
    return FluidSynthObj

def fetch_instrument_tree():
    global InstTree
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
InstTree = None

class FluidWidget(urwid.TreeWidget):
    unexpanded_icon = urwid.AttrMap(urwid.TreeWidget.unexpanded_icon, 'dirmark')
    expanded_icon = urwid.AttrMap(urwid.TreeWidget.expanded_icon, 'dirmark')

    def __init__(self, node):
        super().__init__(node)
        self._w = urwid.AttrWrap(self._w, None)
        self.flagged = False
        self.update_w()

    def selectable(self):
        return True

    def keypress(self, size, key):
        key = super().keypress(size, key)
        if key:
            key = self.unhandled_keys(size, key)
        return key

    def unhandled_keys(self, size, key):
        if key == " ":
            self.flagged = not self.flagged
            self.update_w()
        else:
            return key

    def update_w(self):
        if self.flagged:
            self._w.attr = 'flagged'
            self._w.focus_attr = 'flagged focus'
        else:
            self._w.attr = 'body'
            self._w.focus_attr = 'focus'

class FluidNode(urwid.ParentNode, PathItem):
    attrlist = ('name', 'font', 'bank', 'prog')

    def __init__(self, name='FluidSynth', font=None, bank=None, prog=None, parent=None):
        if InstTree is None:
            fetch_instrument_tree()
        PathItem.__init__(self, font, bank, prog)
        urwid.ParentNode.__init__(self, name, key=self.path, parent=parent)
        self.kids = list()

    def load_child_keys(self):
        return tuple( k for k,v in InstTree.items() if str(v.get_parent()) == str(self) )

    def load_child_node(self, key):
        return InstTree[key]

    def load_widget(self):
        return FluidWidget(self)

    def get_key(self):
        return self.path

class PCFApp:
    palette = [ ('body', 'light gray', 'default'),
                ('head', 'yellow', 'dark blue'),
                ('foot', 'white', 'dark blue'),

                ('dirmark', 'black', 'dark cyan', 'bold'),
                ('focus', 'light gray', 'dark blue', 'standout'),
                ('flagged', 'black', 'dark green', ('bold','underline')),
                ('focus', 'light gray', 'dark blue', 'standout'),
                ('flagged focus', 'yellow', 'dark cyan',
                    ('bold','standout','underline')),
                ('key', 'light cyan', 'black','underline'),
                ('title', 'white', 'black', 'bold'),
                ('error', 'dark red', 'light gray'),
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
