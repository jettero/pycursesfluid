#!/usr/bin/env python
# coding: utf-8

import urwid
from pcf.fluidsynth import FluidSynth
from pcf.misc import PathItem, RangySet

FluidSynthObj = None
def get_fso():
    global FluidSynthObj
    if FluidSynthObj is None:
        FluidSynthObj = FluidSynth()
    return FluidSynthObj

ChanList = InstTree = None
def fetch_current_state():
    global InstTree, ChanList
    fso = get_fso()

    ChanList = fso.channels

    InstTree = dict()
    InstTree['/'] = top = FluidNode('FluidSynth')
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

    for item in InstTree.values():
        item.chan = RangySet()

    for item in ChanList:
        InstTree[ f'/{item.font}/{item.bank}/{item.prog}' ].chan.add(item.chan)

class FluidWidget(urwid.TreeWidget):
    def __init__(self, node):
        super().__init__(node)
        self._w = urwid.AttrWrap(self._w, None)
        self.flagged = False
        self.update_w()

    def get_display_text(self):
        n = self.get_node()
        txt = n.name
        if n.chan:
            ar = ', '.join([ '-'.join([ str(x) for x in i ]) for i in n.chan.as_ranges() ])
            txt += f' [{ar}]'
        if n.prog is not None:
            return ('inst', txt)
        if n.bank is not None:
            return ('bank', txt)
        if n.font is not None:
            return ('font', txt)
        return ('body', txt)

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
    attrlist = ('!name', 'font', 'bank', 'prog')

    def __init__(self, name='FluidSynth', font=None, bank=None, prog=None, parent=None):
        PathItem.__init__(self, name, font, bank, prog)
        urwid.ParentNode.__init__(self, name, key=self.path, parent=parent)

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
                ('focus', 'white', 'default'),

                ('inst', 'light gray', 'default'),
                ('bank', 'light gray', 'default'),
                ('font', 'light gray', 'default'),
            ]

    def __init__(self):
        fetch_current_state()
        current_node = InstTree[ PathItem(*ChanList[0][2:]).path ]

        self.header = urwid.Text('header')
        self.footer = urwid.Text('footer')
        self.listbox = urwid.TreeListBox(urwid.TreeWalker(current_node))
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
