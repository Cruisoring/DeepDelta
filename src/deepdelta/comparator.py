from collections.abc import Collection
from datetime import datetime
from decimal import Decimal
from functools import singledispatch, lru_cache
from typing import Tuple, Union, Dict, Type, Callable, Any

import logging

logger = logging.getLogger(__name__)


def as_float_str(value: Union[float, int, Decimal, str], precision: int = None) -> str:
    """Convert float number or its string to float first, then to unified string with specified or default digits.

    :param value: the value to be unified to string of specified or default digits.
    :param precision: the digits to be reserved for comparison, must be None or positive integer
    :return: string of number rounded with specified or default digits.
    """
    f_value = float(value)
    if precision == None:
        return f"{{:.{Comparator.DEFAULT_FLOAT_PRECISION}f}}".format(f_value)
    else:
        return f"{{:.{precision}f}}".format(f_value)


def compare_number_with_precision(lhs: Any, rhs: Any, precision: int = None) -> bool:
    """Convert float numbers to string format with specified or default digits, then compare.

    :param lhs: left value to be compared as a number
    :param rhs: right  value to be compared as a number
    :param precision: the digits to be reserved for comparison, must be None or positive integer
    :return: True if lhs and right in strings with same digits are identical, otherwise False.
    """
    return as_float_str(lhs, precision) == as_float_str(rhs, precision)


@lru_cache
def with_precision(precision: int) -> Callable[[Any, Any], bool]:
    """Higher order function to create a method alike compare_number_with_precision with fixed precision.

    :param precision: the digits to be reserved for comparison, shall be 0 or positive integer
    :return: a method alike compare_number_with_precision with fixed precision.
    """
    return lambda lhs, rhs: compare_number_with_precision(lhs, rhs, precision)


class Comparator:

    # the default number of digits for comparison numbers, shall be 0 or positive integer
    DEFAULT_FLOAT_PRECISION: int = 2

    # Update following sets to enumerate all TRUE/FALSE values including case-sensitive strings
    TRUE_VALUES = {True, 'True', 'Yes', 'Y', 'Positive', 1, 'TRUE', 'yes'}
    FALSE_VALUES = {False, 'False', 'No', 'N', 'Negative', 0, 'FALSE', 'no'}

    @staticmethod
    def as_bool(value: Any) -> bool:
        """Convert any value to boolean by checking its existence in TRUE_VALUES or FALSE_VALUES.

        :param value: any known value to be treated as either True/False, case sensitive if it is of string.
        :return: True if the given value is in TRUE_VALUES, False if in FALSE_VALUES.
        :raises: ValueError when the given value ssn't contained in either TRUE_VALUES or FALSE_VALUES.
        """
        if value in Comparator.TRUE_VALUES:
            return True
        elif value in Comparator.FALSE_VALUES:
            return False
        else:
            raise ValueError(f"Cannot convert '{value}' to bool.")

    @staticmethod
    def compare_as_bool_values(lhs: Any, rhs: Any) -> bool:
        """Compare two values by converting them as bool first by calling as_bool()

        :param lhs: left value to be compared.
        :param rhs: right value to be compared.
        :return: True if both converted are equal, otherwise False.
        :raises: ValueError if one cannot be converted.
        """
        return Comparator.as_bool(lhs) == Comparator.as_bool(rhs)

    # Common formats to be used to try to parse string as datetime in sequence, please append/insert preferred formats
    # Notice: avoid including ambiguous formats like %d/%m/%Y and %m/%d/%Y at the same time
    DATETIME_FORMATS = ['%d-%m-%Y %H:%M:%S', '%d-%b-%Y %H:%M:%S', '%d/%m/%Y %H:%M:%S', '%d/%b/%Y %H:%M:%S',
                        '%Y-%m-%d %H:%M:%S', '%Y-%b-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S', '%Y/%b/%d %H:%M:%S',
                        '%Y-%B-%d', '%Y %B %d', '%Y/%B/%d', '%Y-%b-%d', '%Y %b %d', '%Y/%b/%d',
                        "%d/%m/%Y", "%d/%m/%y", "%d/%b/%Y", "%d/%b/%y", '%Y-%m-%d', '%Y %m %d',
                        "%d-%m-%Y", "%d-%m-%y", "%d-%b-%Y", "%d-%b-%y", ]

    # Custom converter, if supplied, to convert any object to datetime
    CUSTOM_TO_DATETIME: Callable[[Any], datetime] = None

    @staticmethod
    def as_datetime(value: Union[str, datetime, Any]) -> datetime:
        """Convert the given value, especially of string type, to datetime with pre-defined format or custom converter.

        :param value: the value to be converted to datetime.
        :return: the converted datetime from the given value.
        :raises: ValueError if the given value is not str or datetime, and no CUSTOM_TO_DATETIME specified.
        """

        # assume the value is of string type, then expected format must be defined in Comparator.DATETIME_FORMATS
        if isinstance(value, str):
            for f in Comparator.DATETIME_FORMATS:
                try:
                    return datetime.strptime(value, f)
                except ValueError as _:
                    continue

            raise ValueError(f"Cannot get datetime from str: '{value}'")
        # the CUSTOM_TO_DATETIME function can be defined to convert any other value to datetime
        elif Comparator.CUSTOM_TO_DATETIME:
            return Comparator.CUSTOM_TO_DATETIME(value)
        # only if CUSTOM_TO_DATETIME is not defined and value is not string type, datetime would be returned as it is
        elif isinstance(value, datetime):
            return value
        else:
            raise ValueError(f"Not implemented for type of {type(value)}")

    @staticmethod
    def compare_as_datetime_values(lhs: Union[str, datetime], rhs: Union[str, datetime]) -> bool:
        """Compare two values by converting them as datetime first by calling as_datetime()

        :param lhs: left value to be compared.
        :param rhs: right value to be compared.
        :return: True if both converted are equal, otherwise False.
        :raises: ValueError if one cannot be converted.
        """
        return Comparator.as_datetime(lhs) == Comparator.as_datetime(rhs)

    @staticmethod
    def compare_with_str(lhs: Any, rhs: Any) -> bool:
        """Compare any value with a string, then compare_any_with_str() would be used to compare any registered value
        accordingly.

        :param lhs: left value to be compared.
        :param rhs: right value to be compared.
        :return: True if both converted are equal, otherwise False.
        :raises:  ValueError if none of them is string.
        """
        if isinstance(lhs, str):
            return compare_any_with_str(rhs, lhs)
        elif isinstance(rhs, str):
            return compare_any_with_str(lhs, rhs)
        else:
            raise ValueError(f"Neither '{lhs}' nor '{rhs}' is str")

    @staticmethod
    def compare_with_none(lhs: None, rhs: Any) -> bool:
        """Compare any value with a None, then compare_any_with_none() would be used to compare any registered value
        accordingly.

        :param lhs: left value to be compared.
        :param rhs: right value to be compared.
        :return: True if both converted are equal, otherwise False.
        :raises: ValueError if none of them is string
        """
        if lhs == None and rhs == None:
            return True
        elif lhs == None:
            return compare_any_with_none(rhs)
        elif rhs == None:
            return compare_any_with_none(lhs)
        else:
            raise ValueError(f"Either lhs or rhs shall be None")


@singledispatch
def compare_any_with_none(value: Any):
    """Use Python equality to None by default, please register concerned type to compare it with None.

    It is possible to register concerned type with compare_any_with_none to perform None equality checking.
    :param value: the value to be equaled with None.
    :return: True if it is Python equality to None, otherwise False.
    """
    return not value


@singledispatch
def compare_any_with_str(other: Any, str_value: str) -> bool:
    """Compare any value with a string value in its str() form.

    :param other: the other value to be compared with a string.
    :param str_value: the string value to be compared.
    :return: True if the str() of the other value is equal to str_value.
    """
    return str(other) == str_value


@compare_any_with_str.register(float)
@compare_any_with_str.register(int)
@compare_any_with_str.register(Decimal)
def compare_number_with_str(other: Union[float, Decimal, int], str_value: str) -> bool:
    """Delegate comparison between numbers to NumberComparator.compare.

    :param other: the other value to be compared with a string.
    :param str_value: the string form of a number to be compared.
    :return: same as calling compare_number_with_precision() with default precision.
    """
    return compare_number_with_precision(other, str_value)


@compare_any_with_str.register(bool)
def compare_bool_with_str(other: bool, str_value: str) -> bool:
    """Convert the str_value as boolean to compare it with the other bool.

    :param other: the other value of boolean type.
    :param str_value: the string to be converted and compared as a boolean.
    :return: True if str_value can be converted to the same boolean, otherwise False.
    """
    return other == Comparator.as_bool(str_value)


@compare_any_with_str.register
def compare_datetime_with_str(other: datetime, str_value: str) -> bool:
    """Convert the str_value as datetime to compare it with the other datetime.

    :param other: the other value of datetime type.
    :param str_value: the string to be converted and compared as a datetime.
    :return: True if str_value can be converted to the same datetime, otherwise False.
    """
    return other == Comparator.as_datetime(str_value)


# the default type-based comparators
DEFAULT_TYPE_COMPARATOR: Dict[Union[Tuple[Type, Type], Type], Callable[[Any, Any], bool]] = {
    (int, float): with_precision(0),
    (int, Decimal): with_precision(0),
    (int, str): with_precision(0),
    (Decimal, float): compare_number_with_precision,
    (Decimal, str): compare_number_with_precision,
    (float, str): compare_number_with_precision,
    (bool, str): compare_bool_with_str,
    str: Comparator.compare_with_str,
    (str, type(None)): Comparator.compare_with_str,
    type(None): Comparator.compare_with_none,
}


def are_equal(lhs: Any, rhs: Any,
              comparators: Dict[Union[Tuple[Type, Type], Type], Callable[[Any, Any], bool]] = None) -> bool:
    """Entrance method to compare any two values based on their types that might be different.

    :param lhs: the left value to be compared.
    :param rhs: the right value to be compared.
    :param comparators: the type(s) based comparators, copy of DEFAULT_TYPE_COMPARATOR would be used if not specified.
    :return: True if the left and right value are treated as equal, otherwise False.
    """
    comparators = comparators or dict(DEFAULT_TYPE_COMPARATOR)
    l_type, r_type = type(lhs), type(rhs)
    if (l_type, r_type) in comparators:
        if (r_type, l_type) in comparators and comparators[(l_type, r_type)] != comparators[(r_type, l_type)]:
            logger.warning(f"'({l_type}, {r_type})' and '({l_type}, {r_type})' might get different result")
        return comparators[(l_type, r_type)](lhs, rhs)
    elif (r_type, l_type) in comparators:
        return comparators[(r_type, l_type)](rhs, lhs)
    elif l_type in comparators:
        if r_type in comparators and comparators[l_type] != comparators[r_type]:
            logger.warning(f"Both '{l_type}' and '{r_type}' has comparator defined, be cautious they are different.")
        return comparators[l_type](lhs, rhs)
    elif r_type in comparators:
        return comparators[r_type](rhs, lhs)
    elif l_type != r_type or issubclass(l_type, Collection):
        return NotImplemented
    else:
        return lhs == rhs


def with_comparators(comparators: Dict[Union[Tuple[Type, Type], Type], Callable[[Any, Any], bool]] = None,
                     none_dif_default: bool = False) -> Callable[[Any, Any], bool]:
    """Higher order function to create a method to compare any two objects based on their types.

    :param comparators: the optional types-based comparators, default as copy of the current DEFAULT_TYPE_COMPARATOR
    :param none_dif_default: effective only when comparators is None:
        if True: exclude NoneTypefrom the copy of DEFAULT_TYPE_COMPARATOR, and make comparing str with None as False;
        if False: avoid in-consistence of comparing str and None
    :return: a are_equal(lhs, rhs, comparators) with typed comparators.
    """
    if not comparators:
        comparators = dict(DEFAULT_TYPE_COMPARATOR)
        if none_dif_default:
            del comparators[type(None)]
            comparators[(str, type(None))] = lambda lhs, rhs: False
        else:
            comparators[(str, type(None))] = lambda lhs, rhs: not lhs and not rhs
    return lambda lhs, rhs: are_equal(lhs, rhs, comparators)

