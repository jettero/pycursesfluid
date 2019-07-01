#!/usr/bin/env python
# coding: utf-8

import socket
import select

from .misc import HandyMatch

class FluidSynth:
    _socket = None

    def __init__(self, port=9800, host='localhost'):
        self.port = port
        self.host = host

    @property
    def shell_socket(self):
        if not self._socket:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect( (self.host, self.port) )
        return self._socket

    @property
    def can_read(self, timeout=0.2):
        rl,_,_ = select.select([self.shell_socket], [], [], timeout)
        return bool(rl)

    def read(self, chunk_size=1024):
        sock = self.shell_socket
        buf = ''
        while self.can_read:
            buf_ = sock.recv(chunk_size)
            if buf_ is None:
                break
            buf += buf_.decode()
        return buf

    def send(self, cmd, chunk_size=1024, end='\n'):
        cmd = cmd.rstrip() + '\n'
        cmd = cmd.encode()
        self.shell_socket.send(cmd)
        return self.read(chunk_size=chunk_size)

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
            '\s+bank\s+(?P<bank>\d+),\s+preset\s+(?P<prog>\d+),\s+(?P<name>.+?)$')
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
