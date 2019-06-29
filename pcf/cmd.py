# coding: utf-8

from .jack import Jack

def run():
    j = Jack()
    j.start()
    j.poll()

    f = Fluid()
    f.start()

    print('need more things to do')
