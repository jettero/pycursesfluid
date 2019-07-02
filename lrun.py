#!/usr/bin/env python
# coding: utf-8

import logging
import pcf.cmd

logging.basicConfig(level=logging.DEBUG, filename='debug.log')

if __name__ == '__main__':
    pcf.cmd.run()
