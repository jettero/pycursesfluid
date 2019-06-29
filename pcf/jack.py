# coding: utf-8

import subprocess
import select
import logging
import fnmatch

from .misc import HandyMatch

log = logging.getLogger(__name__)

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
                lines = out.decode().splitlines()
                for line in lines:
                    log.info('[jack_lsp] %s', line)
                print(out.decode(), end='')

class Jack:
    proc = None

    def __init__(self, realtime=True, softmode=True, backend='alsa', rate=48000,
        period=512, nperiods=2, midi='seq', playback='hw:Intel'):
        self.realtime = realtime
        self.softmode = softmode
        self.backend  = backend
        self.rate     = rate
        self.period   = (period, nperiods)
        self.midi     = midi
        self.playback = playback

    @property
    def status(self):
        if self.proc:
            return JackGraphStatus()

    def start(self):
        if self.proc is None:
            cmd = self.cmd
            log.info('starting jack with %s', cmd)
            self.proc = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

    def stop(self):
        if self.proc is None:
            return
        if self.proc.poll() is not None:
            log.info('$? = %d', self.proc.wait())
            self.proc = None
            return
        log.info('stopping jack')
        self.proc.terminate()
        import time
        time.sleep(1)
        self.stop()

    def __del__(self):
        self.stop()

    @property
    def cmd(self):
        cmd = [ 'jackd' ]

        if self.realtime:
            cmd.append('--realtime') # default
        else:
            cmd.append('--no-realtime') # actually required

        cmd.extend( ('--driver',      self.backend) )
        cmd.extend( ('--rate',        self.rate) )
        cmd.extend( ('--period',      self.period[0]) )
        cmd.extend( ('--nperiods', self.period[1]) )

        if self.softmode:
            cmd.append('--softmode')

        cmd.extend( ('--midi', self.midi) )

        if self.playback:
            cmd.extend( ('--playback', self.playback) )

        return tuple( str(x) for x in cmd )

    def poll(self, timeout=0.2):
        if self.proc.poll() is None:
            while True:
                rl,_,_ = select.select([self.proc.stdout], [], [], timeout)
                if rl:
                    log.info('[jackd] %s', self.proc.stdout.readline().decode().rstrip())
                else:
                    break
