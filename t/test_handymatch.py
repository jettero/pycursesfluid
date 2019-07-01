# coding: utf-8

import pytest
from pcf.misc import HandyMatch

def test_hm_unnamed():
    hm = HandyMatch(r'(a)(ba)')
    assert hm('aba')
    assert tuple(hm) == ('a', 'ba')

def test_hm_named():
    hm = HandyMatch(r'(?P<n1>a)(?P<n2>ba)')
    assert hm('aba')
    assert tuple(hm) == ('a', 'ba')
    nt = hm.as_ntuple()
    assert nt == ('a', 'ba')
    assert nt.n1 == 'a'
    assert nt.n2 == 'ba'

    ntr = hm.as_ntuple('n2', 'n1')
    assert ntr == ('ba', 'a')

def test_hm_short_ntuple():
    hm = HandyMatch(r'(?P<n1>a)(?P<n2>ba)')
    assert hm('aba')
    nt = hm.as_ntuple('n2')
    assert nt == ('ba',)

def test_hm_raises():
    hm = HandyMatch(r'(a)(ba)')

    with pytest.raises(ValueError):
        tuple(hm)
    with pytest.raises(ValueError):
        hm.as_ntuple()

    assert hm('aba')
    assert tuple(hm) == ('a', 'ba')

    assert not hm('booo')

    with pytest.raises(ValueError):
        tuple(hm)
    with pytest.raises(ValueError):
        hm.as_ntuple()

def test_hm_takes_user_input_for_named_tuples():
    hm = HandyMatch(r'(?P<n>a)(?P<m>ba)')
    assert hm('aba')
    nt = hm.as_ntuple('z','m','n', z='blarg')
    assert nt == ('blarg','ba','a')
    assert nt.z == 'blarg'
    assert nt.m == 'ba'
    assert nt.n == 'a'
