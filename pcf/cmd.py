# coding: utf-8

from .jack import Jack

def run():
    j = Jack()
    j.start()
    j.poll()
    j.log_status()

    print('need more things to do')
