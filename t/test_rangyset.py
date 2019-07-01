# coding: utf-8

from pcf.misc import RangySet

def test_rangyset():
    rs = RangySet({1,2,3})
    assert rs.as_ranges() == [ (1,3) ]

    rs = RangySet({1,2,3,6,9,10,12})
    assert rs.as_ranges() == [ (1,3), (6,), (9,10), (12,) ]

    rs = RangySet({1,2,3,9,10})
    assert rs.as_ranges() == [ (1,3), (9,10) ]
