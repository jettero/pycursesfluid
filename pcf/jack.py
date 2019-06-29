# coding: utf-8

import subprocess
import logging

log = logging.getLogger(__name__)

class Jack:
    realtime  = True
    softmode  = True
    backend   = 'alsa'
    rate      = 48000
    period    = (512, 2)
    midi      = 'seq'

    proc = None

    def start(self):
        if self.proc is None:
            cmd = self.cmd
            log.info('starting jack with %s', cmd)
            self.proc = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

    def stop(self):
        if self.proc is not None:
            log.info('stopping jack')
            self.proc.terminate()
            log.info('$? = %d', self.proc.wait())

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

        return tuple( str(x) for x in cmd )
