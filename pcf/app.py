#!/usr/bin/env python
# coding: utf-8

from pcf.fluidsynth import FluidSynth
import urwid

class FluidInstrumentWidget(urwid.TreeWidget):
    pass

class FluidInstrumentNode(urwid.TreeNode):
    def __init__(self, name, font=None, bank=None, prog=None):
        self.name = name
        self.font = font
        self.bank = bank
        self.prog = prog
        super().__init__(name, key=self.get_key(), parent=None, depth=0)

    def load_parent(self):
        pass

    def load_child_keys(self):
        return tuple()

    def load_child_node(self, key):
        ks = key.split('/')
        kw = { k:v for k,v in zip(ks[1:], ('name', 'font','bank','prog')) }
        return FluidSynthNode(**kw)

    def load_widget(self):
        return FluidInstrumentWidget(self)

    def get_key(self):
        ret = list()
        if self.font is not None:
            ret.append(str(self.font))
            if self.bank is not None:
                ret.append(str(self.bank))
                if self.prog is not None:
                    ret.append(str(self.prog))
        return f'/{self.name}' + '/'.join(ret)


class FluidSynthNode(FluidInstrumentNode):
    def __init__(self):
        self.F = FluidSynth()
        super().__init__('FluidSynth')

class PCFApp:
    palette = [ ('body', 'light gray', 'default'),
                ('head', 'yellow', 'dark blue'),
                ('foot', 'white', 'dark blue'),
            ]

    def __init__(self):
        self.header = urwid.Text('header')
        self.footer = urwid.Text('footer')
        self.listbox = urwid.TreeListBox(urwid.TreeWalker(FluidSynthNode()))
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
