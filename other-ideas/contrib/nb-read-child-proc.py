#!/usr/bin/env python
# coding: utf-8

import select
import subprocess

def say_things(*say, sleep=1):
    if not say:
        say = 'one two three'.split()
    say = f'; sleep {sleep}; '.join(f'echo {x}' for x in say)
    return subprocess.Popen(['bash', '-c', say], stdout=subprocess.PIPE)

def read_things(p):
    rl,_,_ = select.select([p.stdout], [], [], 0.1)
    if rl:
        line = p.stdout.readline().decode().rstrip()
        return line

def main():
    p = say_things()
    print('trying to read things')
    while p.poll() is None:
        line = read_things(p)
        if line:
            print("got line:", line)
    print('waitpid:', p.wait())
    print('bye')

if __name__ == '__main__':
    main()
