#!/usr/bin/env python
# coding: utf-8

import logging
import socket
import select
import re

from .misc import HandyMatch

# I use -o 'shell.prompt=fs> ' in my fluidsynth so when I 'nc localhost 9800' I
# can see when I start typing.
MY_PROMPT = re.compile(r'^[^>]*>\s*')
LINE_SPLIT = re.compile(r'[\x0d\x0a]+')
CHUNK_SIZE = 1024*8
TIMEOUT = 0.1

class FluidSynth:
    _socket = None
    log = logging.getLogger('FluidSynth')

    def __init__(self, port=9800, host='localhost',
            chunk_size=CHUNK_SIZE, timeout=TIMEOUT,
            prompt=MY_PROMPT):
        self.port = port
        self.host = host
        self.chunk_size = chunk_size
        self.timeout = timeout
        self.prompt = prompt

    @property
    def shell_socket(self):
        if not self._socket:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect( (self.host, self.port) )
        return self._socket

    @property
    def can_read(self):
        rl,_,_ = select.select([self.shell_socket], [], [], self.timeout)
        return bool(rl)

    def _raw_read(self):
        sock = self.shell_socket
        while self.can_read:
            buf = sock.recv(self.chunk_size)
            if buf is None:
                break
            yield buf

    def _post_read(self, part):
        if self.prompt:
            return self.prompt.sub('', part)
        return part

    def read(self):
        buf = ''
        for chunk in self._raw_read():
            buf += chunk.decode()
            while True:
                bs = LINE_SPLIT.split(buf, 1)
                if len(bs) == 1:
                    break
                buf = bs[1]
                yield self._post_read(bs[0])
        if buf:
            buf = self._post_read(buf.rstrip())
            if buf:
                yield buf

    def send(self, *cmds):
        cmds = [ cmd.rstrip() for cmd in cmds ]
        self.log.debug('send(%s)', cmds)
        self.shell_socket.send( (('\n'.join(cmds)) + '\n').encode() )
        return self.read()

    @property
    def fonts(self):
        _,*fontlines = self.send('fonts').splitlines()
        hm = HandyMatch(r'\s*(?P<id>\d+)\s+(?P<path>\S+)\s*')
        ret = list()
        for fl in fontlines:
            if hm(fl):
                name = hm['path']
                name = name.split('/')[-1]
                if name.endswith('.sf2'):
                    name = name[:-4]
                ret.append(hm.as_ntuple(name=name))
        return sorted(ret, key=lambda x: int(x.id))

    @property
    def channels(self):
        hm = HandyMatch(r'^chan\s+(?P<chan>\d+),\s+sfont\s+(?P<font>\d+),'
            r'\s+bank\s+(?P<bank>\d+),\s+preset\s+(?P<prog>\d+),\s+(?P<name>.+?)$')
        ret = list()
        for cl in self.send('channels -verbose').splitlines():
            if hm(cl):
                ret.append(hm.as_ntuple('chan', 'name', 'font', 'bank','prog'))
        return ret

    def select(self, font=None, bank=None, prog=None, chan=0):
        if isinstance(font, tuple):
            font,bank,prog = font.font, font.bank, font.prog
        self.send(f'select {chan} {font} {bank} {prog}')

    @property
    def instruments(self):
        hm = HandyMatch(r'^\s*0*(?P<bank>\d+)-0*(?P<prog>\d+)\s+(?P<name>.+?)\s*$')
        ret = list()
        for font in self.fonts:
            for il in self.send(f'inst {font.id}').splitlines():
                if hm(il):
                    ret.append(hm.as_ntuple('name', 'font', 'bank', 'prog', font=font.id))
        return sorted(ret, key=lambda x: (int(x.font), int(x.bank), int(x.prog)))
