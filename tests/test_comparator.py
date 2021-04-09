from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from deepdelta.comparator import as_float_str, compare_number_with_precision, with_precision, Comparator, compare_number_with_str, \
    compare_bool_with_str, compare_datetime_with_str, compare_any_with_str, compare_any_with_none, are_equal


def test_as_float_str():
    assert as_float_str('3.32227', 4) == '3.3223'
    assert as_float_str(2, 3) == '2.000'
    assert as_float_str(2.7, 3) == '2.700'
    assert as_float_str(2.83828, 3) == '2.838'
    assert as_float_str(Decimal('2.03838'), 3) == '2.038'
    assert as_float_str(2) == '2.00'
    assert as_float_str(2.1) == '2.10'
    assert as_float_str('2.77738') == '2.78'


def test_compare_number_with_precision():
    assert compare_number_with_precision(2.55, '2.5472', 2) is True
    assert compare_number_with_precision(2, '2.4472', 0) is True
    assert compare_number_with_precision(2, '2.5472', 0) is False
    assert compare_number_with_precision(2.55, '2.5472', 3) is False
    assert compare_number_with_precision(Decimal('+2.54738'), '2.5472', 3) is True


def test_with_precision():
    with_3 = with_precision(3)
    assert with_3(2.55, '2.5472') is False
    assert with_3(2.5502, '2.55033') is True


def test_as_bool():
    assert Comparator.as_bool('Y') is True
    with pytest.raises(ValueError):
        Comparator.as_bool('YES') is False
    Comparator.TRUE_VALUES.add('YES')
    assert Comparator.as_bool('YES') is True


def test_compare_as_bool_values():
    assert Comparator.compare_as_bool_values(True, 1) is True
    assert Comparator.compare_as_bool_values(False, 'False') is True
    assert Comparator.compare_as_bool_values(True, 'Yes') is True
    assert Comparator.compare_as_bool_values('No', 0) is True
    assert Comparator.compare_as_bool_values(0, 1) is False


def test_as_datetime():
    assert Comparator.as_datetime('21/Jul/2020') == datetime(2020, 7, 21)
    assert Comparator.as_datetime('21-07-2020') == datetime(2020, 7, 21)
    assert Comparator.as_datetime('21/07/20') == datetime(2020, 7, 21)


def test_custom_to_datetime():
    Comparator.CUSTOM_TO_DATETIME = lambda int_value: datetime(2020, 7, 1) + timedelta(days=int_value)
    assert Comparator.as_datetime(20) == datetime(2020, 7, 21)
    Comparator.CUSTOM_TO_DATETIME = None


def test_compare_as_datetime_values():
    assert Comparator.compare_as_datetime_values('2020-July-08', '08/Jul/2020') is True
    assert Comparator.compare_as_datetime_values('08-07-2020', '08/Jul/2020') is True
    assert Comparator.compare_as_datetime_values('08/Jul/2020', datetime(2020, 7, 8)) is True
    assert Comparator.compare_as_datetime_values('2020 July 15', '14/Jul/2020') is False


def test_compare_number_with_str():
    assert compare_number_with_str(100, '100.0') is True
    assert compare_number_with_str(100.23, '100.233') is True
    assert compare_number_with_str(Decimal(100), '100.0') is True
    assert compare_number_with_str(100.24, '100.233') is False
    assert compare_number_with_str(Decimal(100), '101') is False


def test_compare_bool_with_str():
    assert compare_bool_with_str(True, 'True') is True
    assert compare_bool_with_str(True, 1) is True
    assert compare_bool_with_str(True, 'Yes') is True
    assert compare_bool_with_str(True, 0) is False
    assert compare_bool_with_str(True, 'False') is False
    assert compare_bool_with_str(True, 'No') is False
    assert compare_bool_with_str(True, 'N') is False


def test_compare_datetime_with_str():
    assert compare_datetime_with_str(datetime(2020, 10, 1), '2020-Oct-01') is True
    assert compare_datetime_with_str(datetime(2020, 10, 1, 13, 15, 6), '2020-Oct-01 13:15:06') is True


def test_compare_any_with_str():
    assert compare_any_with_str(100, '100.0') is True
    assert compare_any_with_str(True, 0) is False
    assert compare_any_with_str(datetime(2020, 10, 1), '2020-Oct-01') is True
    assert compare_any_with_str([], '[]') is True
    assert compare_any_with_str([0], '[]') is False


def test_compare_with_str():
    assert Comparator.compare_with_str(100, '100.0') is True
    assert Comparator.compare_with_str('100', Decimal(100.0)) is True
    assert Comparator.compare_with_str('3', 3) is True
    assert Comparator.compare_with_str(True, 'Yes') is True
    assert Comparator.compare_with_str(datetime(2020, 10, 1), '2020-Oct-01') is True


def test_compare_any_with_none_python_none_equality():
    assert compare_any_with_none([]) is True
    assert compare_any_with_none({}) is True
    assert compare_any_with_none(()) is True
    assert compare_any_with_none(0) is True
    assert compare_any_with_none(0.0) is True


def test_compare_with_none_python_none_equality():
    assert Comparator.compare_with_none(None, 0) is True
    assert Comparator.compare_with_none(None, []) is True
    assert Comparator.compare_with_none(0.0, None) is True
    assert Comparator.compare_with_none((), None) is True
    assert Comparator.compare_with_none(None, None) is True

    assert Comparator.compare_with_none(None, -1) is False
    assert Comparator.compare_with_none(None, [()]) is False
    assert Comparator.compare_with_none(0.0000001, None) is False
    assert Comparator.compare_with_none((1, 2, 3), None) is False
    assert Comparator.compare_with_none(None, [None]) is False

    with pytest.raises(ValueError):
        Comparator.compare_with_none({}, [])


def test_compare_any_with_none_custom_comparer():
    """A test showing how to register any type to compare with None."""
    @compare_any_with_none.register(list)
    def compare_list_with_none(other: list) -> bool:
        if not other:
            return True
        elif all((not item for item in other)):
            return True
        else:
            return False
    assert Comparator.compare_with_none(None, [None]) is True
    assert Comparator.compare_with_none([0, 0.0, False, {}, (), []], None) is True


def test_are_equal():
    assert are_equal(True, 'Positive') is True
    assert are_equal('Yes', True) is True
    assert are_equal(1.0277, '+1.02773') is True
    assert are_equal(6.07, 6) is True
    assert are_equal(True, True) is True
    assert are_equal(Decimal('2.7777'), '2.7778') is True
    assert are_equal([], None) is True

    assert are_equal(True, None) is False
    assert are_equal(False, None) is True
    assert are_equal(None, False) is True
    assert are_equal('None', None) is True
    assert are_equal(None, 'None') is True
