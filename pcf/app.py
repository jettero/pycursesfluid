#!/usr/bin/env python
# coding: utf-8

import time
import logging
import urwid
from pcf.fluidsynth import FluidSynth
from pcf.misc import PathItem, RangySet
from pcf.metronome import Metronome

WALTZ = ( ((35,50), (45,33), (46,33)),
          ((35,33),),
          ((35,33),),
        )
ROCK = WALTZ + WALTZ[-1]

class FluidInstrumentWidget(urwid.TreeWidget):
    log = logging.getLogger('FluidInstrumentWidget')

    def __init__(self, node):
        super().__init__(node)
        self._w = urwid.AttrWrap(self._w, None)
        self.flagged = False
        self.update_w()

    def selectable(self):
        return True

    def fold(self):
        self.expanded = False
        self.update()

    def unfold(self):
        self.expanded = True
        self.update()

    def get_display_text(self):
        n = self.get_node()
        txt = n.name
        if n.chan:
            ar = ', '.join([ '-'.join([ str(x) for x in i ]) for i in n.chan.as_ranges() ])
            txt += f' [{ar}]'
        self.log.debug("get_display_text() → %s", txt)
        return txt

    def update(self):
        iw = self.get_inner_widget()
        iw.set_text( self.get_display_text() )
        # definitely not convinced all this invalidating and updating is
        # necessary, but when urwid starts to work, you roll with it.
        iw._invalidate()
        self._invalidate()
        self.update_w()
        self.update_expanded_icon()

    def update_w(self):
        if self.get_node().chan:
            self._w.attr = 'flagged'
            self._w.focus_attr = 'flagged focus'
        else:
            self._w.attr = 'body'
            self._w.focus_attr = 'focus'

class FluidInstrumentNode(urwid.TreeNode, PathItem):
    log = logging.getLogger('FluidInstrumentNode')
    attrlist = ('!name', 'font', 'bank', 'prog')

    def __init__(self, name='FluidSynth', font=None, bank=None, prog=None, parent=None):
        PathItem.__init__(self, name, font, bank, prog)
        urwid.TreeNode.__init__(self, name, key=self.path, parent=parent)
        self.chan = RangySet()

        if parent is not None:
            parent.set_child_node(self.path, self)

    def load_widget(self):
        return FluidInstrumentWidget(self)

    def _invalidate(self):
        self.get_widget().update()
        # w = self.get_widget()
        # w._invalidate()
        # w.get_inner_widget()

class FluidFontNode(FluidInstrumentNode, urwid.ParentNode):
    log = logging.getLogger('FluidFontNode')
    attrlist = ('!name', 'font', 'bank', 'prog')

    def __init__(self, name='FluidSynth', font=None, bank=None, prog=None, parent=None):
        PathItem.__init__(self, name, font, bank, prog)
        urwid.ParentNode.__init__(self, name, key=self.path, parent=parent)

        if parent is not None:
            parent.set_child_node(self.path, self)

    def get_child_keys(self):
        return tuple(self._children.keys())

    @property
    def chan(self):
        ret = RangySet()
        for k in self.get_child_keys():
            n = self.get_child_node(k)
            for i in n.chan:
                ret.add(i)
        return ret

ACTUAL_SHOW_CURSOR = urwid.escape.SHOW_CURSOR
class PCFApp:
    log = logging.getLogger('PCFApp')
    palette = [ ('body', 'light gray', 'default'),
                ('head', 'light gray', 'dark blue'),
                ('foot', 'light gray', 'dark blue'),
                ('button', 'light red', 'dark blue'),
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
        self.mouse_bookmarks = set()
        self.reload()

        self.listbox  = urwid.TreeListBox(self.walker)
        self.header   = urwid.Text('FluidSynth Instruments')
        self.channels = urwid.Text('')
        self.help     = urwid.Text('')
        self.footer   = urwid.Columns([
            urwid.Padding( self.help, 'left', width=('relative', 100) ),
            urwid.Padding( self.channels, 'right', width=16, min_width=16 ),
        ])

        la = urwid.AttrWrap(self.listbox, 'body')
        ha = urwid.AttrWrap(self.header,  'head')
        fa = urwid.AttrWrap(self.footer,  'foot')

        self.view = urwid.Frame( la, header=ha, footer=fa )

        self.metronome = None
        self.beats_per_minute = 75

        self.update_footer()

    def reload(self, fetch=True):
        if fetch:
            self.fetch_current_state()
        self.build_inst_tree()

        cur_node = self.current_node
        if cur_node:
            start_key = cur_node.path
        else:
            start_key = '/'
            # start_key = PathItem(*self.chan_list[0][2:]).path

        self.start_key = start_key
        self.start_node = self.inst_tree[ start_key ]

        self.walker = urwid.TreeWalker(self.start_node)
        if self.listbox is not None:
            self.listbox.body = self.walker

        for node in self.inst_tree.values():
            if isinstance(node, FluidFontNode) and not node in (self.top_node, self.start_node, self.start_node.get_parent()):
                node.get_widget().fold()

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

    def update_footer(self, msg=None):
        if msg is None:
            time.sleep(0.5)
            msg = [
                ('button', '<spc>'), ('foot', ':set-inst '),
                ('button', '0…f'), ('foot', ':±chan '),
                ('button', '_'), ('foot', ':-all '),
                ('button', '+'), ('foot', ':+all '),
                ('button', 'r'), ('foot', ':reload '),
                ('button', '$'), ('foot', ':4/4 beat '),
                ('button', '#'), ('foot', ':3/4 beat '),
                ('button', '['), ('foot', ':-15 bpm '),
                ('button', ']'), ('foot', ':+15 bpm '),
            ]
        elif msg is not None:
            msg = ('foot', msg)
        attr_txt = list()
        for i in range(16):
            c = 'active' if i in self.active_channels else 'inactive'
            attr_txt.append( (c,f'{i:x}') )
        self.channels.set_text( attr_txt )
        if msg is not None:
            self.help.set_text( msg )
        if hasattr(self, 'loop'):
            self.loop.draw_screen()

    def push_current_node_to_active_channels(self):
        cur_node = self.current_node
        self.update_footer(f'→ setting active channels → {cur_node.full_string} … ')
        for chan in self.active_channels:
            if chan in cur_node.chan:
                continue
            self.fso.select( cur_node.font, cur_node.bank, cur_node.prog, chan=chan )
            cur_node.chan.add(chan)
            self.log.debug('added chan=%s to %s', chan, cur_node)
            cur_node._invalidate()
            for itn in self.inst_tree.values():
                if itn is not cur_node and chan in itn.chan:
                    self.log.debug("chan=%s went to %s, removed from %s", chan, cur_node, itn)
                    itn.chan.remove(chan)
                    itn._invalidate()
        self.update_footer()

    def unhandled_input(self, k):
        self.log.debug('unhandled_input(%s)', k)
        if isinstance(k, tuple):
            ev,button,col,row = k
            # if ev == 'mouse press' and button == 1:
            #     self.mouse_bookmarks.add('+')
            # elif ev == 'mouse release' and '+' in self.mouse_bookmarks:
            #     self.mouse_bookmarks.remove('+')
            #     self.active_channels = set(int(x) for x in self.current_node.chan)
            #     self.update_footer()

        else:
            if k in ('q', 'Q'):
                raise urwid.ExitMainLoop()

            elif k == '#':
                if self.metronome:
                    self.metronome.stop()
                    self.metronome = None
                else:
                    self.metronome = Metronome(*WALTZ,
                        beats_per_minute=self.beats_per_minute)
                    self.metronome.start()

            elif k == '$':
                if self.metronome:
                    self.metronome.stop()
                    self.metronome = None
                else:
                    self.metronome = Metronome(*ROCK,
                        beats_per_minute=self.beats_per_minute)
                    self.metronome.start()

            elif k == '[':
                self.beats_per_minute -= 15
                self.update_footer(f'{self.beats_per_minute} bpm')
                self.update_footer()
                if self.metronome:
                    self.metronome.stop()
                    self.metronome.beats_per_minute = self.beats_per_minute
                    self.metronome.start()

            elif k == ']':
                self.beats_per_minute += 15
                self.update_footer(f'{self.beats_per_minute} bpm')
                self.update_footer()
                if self.metronome:
                    self.metronome.stop()
                    self.metronome.beats_per_minute = self.beats_per_minute
                    self.metronome.start()

            elif k == 'r':
                self.update_footer(f'reloading …')
                self.reload()
                self.update_footer()

            elif k in ('+', '='):
                self.active_channels = set(range(16))
                self.update_footer()
            elif k in ('-', '_'): # '-' doesn't actually work, it's a default binding for something else
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
                self.push_current_node_to_active_channels()

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
        self.inst_tree['/'] = self.top_node = FluidFontNode('FluidSynth')

        # add soundfont nodes
        for font,name,path in self.font_list:
            n = FluidFontNode(path, font, parent=self.top_node)
            self.inst_tree[n.path] = n

        # add instrument nodes
        for name,font,bank,prog in self.inst_list:
            fp = PathItem(font).path
            n = FluidInstrumentNode(f'{int(bank):03d}-{int(prog):03d} {name}',
                font,bank,prog, parent=self.inst_tree[fp])
            self.inst_tree[n.path] = n

        # mark all instruments with their channel(s) (if any)
        for chan,_,*fbp in self.chan_list:
            self.inst_tree[ PathItem(*fbp).path ].chan.add(chan)
