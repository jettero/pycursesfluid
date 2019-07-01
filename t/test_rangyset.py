# coding: utf-8

from pcf.misc import RangySet

def test_rangyset():
    rs = RangySet({1,2,3})
    assert rs.as_ranges() == [ (1,3) ]

    rs = RangySet({1,2,3,6,9,10,12})
    assert rs.as_ranges() == [ (1,3), (6,), (9,10), (12,) ]

    rs = RangySet({1,2,3,9,10})
    assert rs.as_ranges() == [ (1,3), (9,10) ]

def test_stupid_strings_though():
    rs = RangySet(set( x for x in range(1,15) ))
    assert rs.as_ranges() == [ (1,14) ]

    rs = RangySet(set( str(x) for x in range(1,15) ))
    assert rs.as_ranges() == [ (1,14) ]
