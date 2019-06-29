#!/usr/bin/env python
# coding: utf-8

# Not a proper entry point, just used for testing.

if __name__ == '__main__':
    import logging
    import pcf.cmd

    logging.basicConfig(level=logging.DEBUG)

    pcf.cmd.run()
