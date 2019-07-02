#!/usr/bin/env python
# coding: utf-8

import logging
import urwid
from pcf.fluidsynth import FluidSynth
from pcf.misc import PathItem, RangySet

class FluidWidget(urwid.TreeWidget):
    log = logging.getLogger('FluidWidget')

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

    def update_w(self):
        if self.get_node().chan:
            self._w.attr = 'flagged'
            self._w.focus_attr = 'flagged focus'
        else:
            self._w.attr = 'body'
            self._w.focus_attr = 'focus'


class FluidNode(urwid.ParentNode, PathItem):
    log = logging.getLogger('FluidNode')
    attrlist = ('!name', 'font', 'bank', 'prog')

    def __init__(self, name='FluidSynth', font=None, bank=None, prog=None, parent=None):
        PathItem.__init__(self, name, font, bank, prog)
        urwid.ParentNode.__init__(self, name, key=self.path, parent=parent)
        self.chan = RangySet()

        if parent is not None:
            parent.set_child_node(self.path, self)

    def get_child_keys(self):
        return tuple(self._children.keys())

    def load_widget(self):
        return FluidWidget(self)


class PCFApp:
    log = logging.getLogger('PCFApp')
    palette = [ ('body', 'light gray', 'default'),
                ('head', 'yellow', 'dark blue'),
                ('foot', 'white', 'dark blue'),
                ('focus', 'white', 'default'),

                ('inst', 'light gray', 'default'),
                ('bank', 'light gray', 'default'),
                ('font', 'light gray', 'default'),
            ]

    _fso = font_list = chan_list = inst_list = None # class vars
    listbox = walker = inst_tree = None # instance var

    def __init__(self):
        self.reload() # populates self.walker
        # iff self.listbox is populated, reload sets self.listbox.body = self.walker

        self.header = urwid.Text('header')
        self.footer = urwid.Text('footer')
        self.listbox = urwid.TreeListBox(self.walker)

        self.view = urwid.Frame(
            urwid.AttrWrap(self.listbox, 'body'),
            header=urwid.AttrWrap(self.header, 'head'),
            footer=urwid.AttrWrap(self.footer, 'foot'))

    def reload(self):
        self.fetch_current_state()
        self.build_inst_tree()

    def main(self):
        self.loop = urwid.MainLoop(self.view, self.palette, unhandled_input=self.unhandled_input)
        try:
            self.loop.run()
        except KeyboardInterrupt:
            pass
        print('\nbye.\n')

    def unhandled_input(self, k):
        if k in ('q', 'Q'):
            raise urwid.ExitMainLoop()

    @property
    def fso(self):
        return self.get_fso()

    @classmethod
    def get_fso(cls):
        if cls._fso is None:
            cls._fso = FluidSynth()
        return cls._fso

    def fetch_current_state(cls):
        cls.log.debug('fetch_current_state()')
        fso = cls.get_fso()
        cls.font_list = fso.fonts
        cls.chan_list = fso.channels
        cls.inst_list = fso.instruments

    def build_inst_tree(self):
        # reset tree
        self.inst_tree = dict()
        self.inst_tree['/'] = top = FluidNode('FluidSynth')

        # add soundfont nodes
        for font,name,path in self.font_list:
            n = FluidNode(path, font, parent=top)
            self.inst_tree[n.path] = n

        # add instrument bank nodes
        for name,font,bank,_ in self.inst_list:
            fp = PathItem(font).path
            bp = PathItem(font,bank).path
            if bp in self.inst_tree:
                continue
            self.inst_tree[bp] = FluidNode(f'Bank-{bank}', font,bank, parent=self.inst_tree[fp])

        # add instrument nodes
        for name,font,bank,prog in self.inst_list:
            bp = PathItem(font,bank).path
            n = FluidNode(name, font,bank,prog, parent=self.inst_tree[bp])
            self.inst_tree[n.path] = n

        # mark all instruments with their channel(s) (if any)
        for chan,_,*fbp in self.chan_list:
            self.inst_tree[ PathItem(*fbp).path ].chan.add(chan)

        self.start_node = self.inst_tree[ PathItem(*self.chan_list[0][2:]).path ]
        self.walker = urwid.TreeWalker(self.start_node)
        if self.listbox is not None:
            self.listblox.body = self.walker
