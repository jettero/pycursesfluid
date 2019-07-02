# coding: utf-8

from pcf.misc import PathItem

def test_empty_fluid_pathitem():
    fpi = PathItem()

    assert str(fpi) == '/'
    assert tuple(fpi) == tuple()

def test_named_empty_pathitem():
    fpi = PathItem('named')

    assert str(fpi) == '/named'
    assert tuple(fpi) == ('named',)

def test_named_font_pathitem():
    fpi = PathItem('named', 0)

    assert str(fpi) == '/named/0'
    assert tuple(fpi) == ('named', 0)

def test_named_font_bank_pathitem():
    fpi = PathItem('named', 0, 1)

    assert str(fpi) == '/named/0/1'
    assert tuple(fpi) == ('named', 0, 1)

def test_named_font_bank_prog_pathitem():
    fpi = PathItem('named', 0, 1, 32)

    assert str(fpi) == '/named/0/1/32'
    assert tuple(fpi) == ('named', 0, 1, 32)
