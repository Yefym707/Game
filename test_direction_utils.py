import pytest

from game import normalize_direction, direction_to_offset


def test_normalize_direction_aliases():
    assert normalize_direction('North') == 'w'
    assert normalize_direction('LEFT') == 'a'
    # short hand letters
    assert normalize_direction('n') == 'w'
    assert normalize_direction('e') == 'd'
    # unknown value returns lowercased input
    assert normalize_direction('Upleft') == 'upleft'


def test_direction_to_offset():
    assert direction_to_offset('north') == (0, -1)
    assert direction_to_offset('e') == (1, 0)
    # unsupported direction returns None
    assert direction_to_offset('upleft') is None
