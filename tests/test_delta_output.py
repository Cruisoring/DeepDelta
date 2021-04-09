from typing import Any

from deepdelta.delta_config import DeltaConfig
from deepdelta.delta_output import DeltaOutput, get_output, Output_Buffer, set_output


def test_get_value_abbrev():
    assert DeltaOutput.get_value_abbrev(None) is None
    assert DeltaOutput.get_value_abbrev(7.32) == 7.32
    assert DeltaOutput.get_value_abbrev([]) == '[...]'
    assert DeltaOutput.get_value_abbrev(set()) == '{,,}'
    assert DeltaOutput.get_value_abbrev({}) == '{...}'
    assert DeltaOutput.get_value_abbrev(tuple()) == '(...)'


def test_no_flag_tuple_abbrev():
    assert DeltaOutput.no_flag_tuple_abbrev(True, [], {}) == ('[...]', '{...}')
    assert DeltaOutput.no_flag_tuple_abbrev(True, True, False) == (True, False)
    assert DeltaOutput.no_flag_tuple_abbrev(True, 3.23, {'pass': False}) == (3.23, '{...}')
    assert DeltaOutput.no_flag_tuple_abbrev(True, (3.23,), 3.23) == ('(...)', 3.23)
    assert DeltaOutput.no_flag_tuple_abbrev(False, [], {}) is None
    assert DeltaOutput.no_flag_tuple_abbrev(False, 3.27, '2.11') is None


def test_as_tuple():
    assert DeltaOutput.as_tuple(True, [], {}) == (True, [], {})
    assert DeltaOutput.as_tuple(True, True, False) == (True, True, False)
    assert DeltaOutput.as_tuple(True, 3.23, {'pass': False}) == (True, 3.23, {'pass': False})
    assert DeltaOutput.as_tuple(True, (3.23,), 3.23) == (True, (3.23,), 3.23)
    assert DeltaOutput.as_tuple(False, [], {}) == (False, [], {})
    assert DeltaOutput.as_tuple(False, 3.27, '2.11') == (False, 3.27, '2.11')


def test_as_none_or_tuple():
    assert DeltaOutput.as_none_or_tuple(True, [], {}) == ([], {})
    assert DeltaOutput.as_none_or_tuple(True, True, False) == (True, False)
    assert DeltaOutput.as_none_or_tuple(True, 3.23, {'pass': False}) == (3.23, {'pass': False})
    assert DeltaOutput.as_none_or_tuple(True, (3.23,), 3.23) == ((3.23,), 3.23)
    assert DeltaOutput.as_none_or_tuple(False, [], {}) is None
    assert DeltaOutput.as_none_or_tuple(False, 3.27, '2.11') is None


def test_type_included():
    assert DeltaOutput.type_included(True, [], {}) == (True, [], {}, list, dict)
    assert DeltaOutput.type_included(True, True, False) == (True, True, False, bool, bool)
    assert DeltaOutput.type_included(True, 3.23, {'pass': False}) == (True, 3.23, {'pass': False}, float, dict)
    assert DeltaOutput.type_included(True, (3.23,), 3.23) == (True, (3.23,), 3.23, tuple, float)
    assert DeltaOutput.type_included(False, [], {}) == (False, [], {}, list, dict)
    assert DeltaOutput.type_included(False, 3.27, '2.11') == (False, 3.27, '2.11', float, str)


def test_as_none_or_str():
    assert DeltaOutput.as_none_or_str(True, [], {}) == '[...] | {...}'
    assert DeltaOutput.as_none_or_str(True, True, False) == 'True | False'
    assert DeltaOutput.as_none_or_str(True, 3.23, {'pass': False}) == "3.23 | {...}"
    assert DeltaOutput.as_none_or_str(True, (3.23,), 3.23) == "(...) | 3.23"
    assert DeltaOutput.as_none_or_str(False, [], {}) is None
    assert DeltaOutput.as_none_or_str(False, 3.27, '2.11') is None


def test_as_none_or_str_raw():
    assert DeltaOutput.as_none_or_str_raw(True, [], {}) == '[] | {}'
    assert DeltaOutput.as_none_or_str_raw(True, True, False) == 'True | False'
    assert DeltaOutput.as_none_or_str_raw(True, 3.23, {'pass': False}) == "3.23 | {'pass': False}"
    assert DeltaOutput.as_none_or_str_raw(True, (3.23,), 3.23) == "(3.23,) | 3.23"
    assert DeltaOutput.as_none_or_str_raw(False, [], {}) is None
    assert DeltaOutput.as_none_or_str_raw(False, 3.27, '2.11') is None


def test_as_none_or_dict():
    assert DeltaOutput.as_none_or_dict(True, [], {}) == {'LEFT': '[...]', 'RIGHT': '{...}'}
    assert DeltaOutput.as_none_or_dict(True, True, False) == {'LEFT': True, 'RIGHT': False}
    assert DeltaOutput.as_none_or_dict(True, 3.23, {'pass': False}) == {'LEFT': 3.23, 'RIGHT': '{...}'}
    assert DeltaOutput.as_none_or_dict(True, (3.23,), 3.23) == {'LEFT': '(...)', 'RIGHT': 3.23}
    assert DeltaOutput.as_none_or_dict(False, [], {}) is None
    assert DeltaOutput.as_none_or_dict(False, 3.27, '2.11') is None


def test_as_none_or_dict_raw():
    assert DeltaOutput.as_none_or_dict_raw(True, [], {}) == {'LEFT': [], 'RIGHT': {}}
    assert DeltaOutput.as_none_or_dict_raw(True, True, False) == {'LEFT': True, 'RIGHT': False}
    assert DeltaOutput.as_none_or_dict_raw(True, 3.23, {'pass': False}) == {'LEFT': 3.23, 'RIGHT': {'pass': False}}
    assert DeltaOutput.as_none_or_dict_raw(True, (3.23,), 3.23) == {'LEFT': (3.23,), 'RIGHT': 3.23}
    assert DeltaOutput.as_none_or_dict_raw(False, [], {}) is None
    assert DeltaOutput.as_none_or_dict_raw(False, 3.27, '2.11') is None


def custom_output(is_dif: bool, left: Any, right: Any) -> dict:
    d = {'Delta': is_dif, 'OLD': DeltaOutput.get_value_abbrev(left) if left else "MISSING OLD",
         'New': DeltaOutput.get_value_abbrev(right) if right else "MISSING New"}
    return d


def test_customised_output():
    set_output(DeltaConfig.OutputDeltaAsCustom, custom_output)
    try:
        assert DeltaConfig.OutputDeltaAsCustom in Output_Buffer
        output = get_output(DeltaConfig.OutputDeltaAsCustom)
        assert output(True, 3.22, '3.27') == {"Delta": True, 'OLD': 3.22, 'New': '3.27'}
        assert output(True, 3.22, '') == {"Delta": True, 'OLD': 3.22, 'New': 'MISSING New'}
        assert output(True, 0, '3.27') == {"Delta": True, 'OLD': 'MISSING OLD', 'New': '3.27'}
        assert output(True, 3.22, ['3.27']) == {"Delta": True, 'OLD': 3.22, 'New': '[...]'}
        assert output(False, 3.22, '3.27') == {"Delta": False, 'OLD': 3.22, 'New': '3.27'}
        assert output(False, 3.22, '3.22') == {"Delta": False, 'OLD': 3.22, 'New': '3.22'}
    finally:
        del Output_Buffer[DeltaConfig.OutputDeltaAsCustom]
