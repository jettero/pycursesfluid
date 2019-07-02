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
        return txt

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


ACTUAL_SHOW_CURSOR = urwid.escape.SHOW_CURSOR
class PCFApp:
    log = logging.getLogger('PCFApp')
    palette = [ ('body', 'light gray', 'default'),
                ('head', 'light gray', 'dark blue'),
                ('foot', 'light gray', 'dark blue'),
                ('flagged', 'dark green', 'default'),
                ('focus', 'white', 'dark gray'),
                ('flagged focus', 'light green', 'dark gray'),
                ('active', 'white', 'dark blue'),
                ('inactive', 'dark gray', 'dark blue'),
            ]

    _fso = font_list = chan_list = inst_list = None # class vars

    def __init__(self):
        self.start_node = self.listbox = self.walker = self.inst_tree = None
        self.active_channels = {0,}
        self.mouse_bookmarks = list()
        self.reload()

        self.listbox = urwid.TreeListBox(self.walker)
        self.header  = urwid.Text('FluidSynth Instruments')
        self.footer  = urwid.Text('')

        la = urwid.AttrWrap(self.listbox, 'body')
        ha = urwid.AttrWrap(self.header,  'head')
        fa = urwid.AttrWrap(self.footer,  'foot')

        self.view = urwid.Frame( la, header=ha, footer=fa )

        self.update_footer()

    def reload(self):
        self.fetch_current_state()
        self.build_inst_tree()

        cur_node = self.current_node
        if cur_node:
            start_key = cur_node.path
        else:
            start_key = PathItem(*self.chan_list[0][2:]).path

        self.start_node = self.inst_tree[ start_key ]

        self.walker = urwid.TreeWalker(self.start_node)
        if self.listbox is not None:
            self.listbox.body = self.walker

    def main(self):
        urwid.escape.SHOW_CURSOR = ''
        self.loop = urwid.MainLoop(self.view, self.palette, unhandled_input=self.unhandled_input)
        try:
            self.loop.run()
        except KeyboardInterrupt:
            pass
        finally:
            urwid.escape.SHOW_CURSOR = ACTUAL_SHOW_CURSOR
            self.loop.screen.write(urwid.escape.SHOW_CURSOR)
            print('\nbye.\n')

    @property
    def current(self):
        try:
            return self.listbox.body.get_focus()
        except AttributeError:
            pass

    @property
    def current_node(self):
        try:
            return self.current[1]
        except TypeError:
            pass

    def update_footer(self, *msg, draw_now=None):
        attr_txt = list()
        for i in range(16):
            c = 'active' if i in self.active_channels else 'inactive'
            attr_txt.append( (c,f'{i:x}') )
        for m in msg:
            attr_txt += [ '  ', ('foot', m) ]
        self.footer.set_text( attr_txt )
        if msg and draw_now is None:
            draw_now = True
        if draw_now:
            self.loop.draw_screen()

    def unhandled_input(self, k):
        self.log.debug('unhandled_input(%s)', k)
        if isinstance(k, tuple):
            ev,button,col,row = k
        else:
            if k in ('q', 'Q'):
                raise urwid.ExitMainLoop()

            elif k == '=':
                self.active_channels = set(range(16))
                self.update_footer()
            elif k == '_':
                self.active_channels.clear()
                self.update_footer()

            elif k in '0123456789abcdef':
                k = int(k, 16)
                if k in self.active_channels:
                    self.active_channels.remove(k)
                else:
                    self.active_channels.add(k)
                self.update_footer()

            elif k == ' ':
                cur_node = self.current_node
                for chan in self.active_channels:
                    self.fso.select( cur_node.font, cur_node.bank, cur_node.prog, chan=chan )
                self.update_footer(f'setting active_channels to {cur_node.full_string} … ')
                self.reload()
                self.update_footer()

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
