# coding: utf-8

import pytest
from pcf.fluidsynth import FluidSynth

FS = FluidSynth()
pretest = list()
try:
    pretest = list(FS.send('echo test'))
except:
    pass

@pytest.mark.skipif(not pretest or pretest[0] != 'test',
    reason="prolly FS isn't running or isn't on the default port")
def test_fs():
    res = list(FS.send('echo test1', 'echo test2', 'echo test3'))
    assert res == ['test1', 'test2', 'test3']
