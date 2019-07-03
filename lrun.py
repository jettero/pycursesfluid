#!/usr/bin/env python
# coding: utf-8

import logging
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

import pcf.cmd

logging.basicConfig( level=logging.DEBUG, filename='debug.log',
    format='%(asctime)s %(name)17s %(levelname)5s %(message)s', datefmt='%H:%M:%S')

if __name__ == '__main__':
    pcf.cmd.run()
