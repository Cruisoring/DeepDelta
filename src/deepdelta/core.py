#!/usr/bin/env python3
from __future__ import annotations
from datetime import datetime, date
import re
from decimal import Decimal
from functools import singledispatch
from typing import List, Tuple, Pattern, Union, Any, Mapping, Dict, Sequence, Callable, Set, Type, Collection

from deepdelta.comparator import with_comparators
from deepdelta.delta_config import DeltaConfig
from deepdelta.delta_output import get_output

# from .delta_config import DeltaConfig
# from .comparator import DEFAULT_TYPE_COMPARATOR, Comparator
# from .delta_output import TYPE_ABBREVIATIONS, DeltaOutput, Output_Buffer

import logging

logger = logging.getLogger(__name__)


"""DeltaConfig to be used by default to:
1) Ignore cases of key and value
2) Trim spaces of keys before comparison
3) Try to use the IDs as keys to convert list to dict
4) Missing of a key is treated as if its value is defined as None
5) Output in default format: Deltas as tuples of (left_value, right_value) if values are different, otherwise None    
"""
DEFAULT_DELTA_CONFIG: DeltaConfig = DeltaConfig.CaseIgnored\
                                    | DeltaConfig.SpaceTrimmed\
                                    | DeltaConfig.IdAsKey \
                                    | DeltaConfig.MissingAsNone \
                                    | DeltaConfig.OutputDefault


@singledispatch
def key_matches(kp, key_path: str, case_ignored=False) -> bool:
    """With a given key path, check if the concerned key is matched or not.

    :param kp: Key string or Pattern to be matched
    :param key_path: The key path used to get the right keys, shall be in form of '>key1', '>k1>k2' and etc.
    :param case_ignored: True for case in-sensitive comparison, False for case sensitive.
    :return: True if the given Key string or Pattern matched with the key path, otherwise False.
    :raises: TypeError if the kp is not re.Pattern or str.
    """
    return key_matches(str(kp), key_path, case_ignored)


@key_matches.register(tuple)
def _(tpl: Tuple, key_path: str, case_ignored=False) -> bool:
    """Called when the concerned Key is defined as a tuple to see if they are matched."""
    return normalize(tpl, case_ignored) == key_path


@key_matches.register(re.Pattern)
def _(pattern, key_path: str, case_ignored=False) -> bool:
    """Called when the concerned Key is defined as a re.Pattern, and case_ignored flag is neglected."""
    return re.fullmatch(pattern, key_path) is not None


@key_matches.register(str)
def _(key, key_path: str, case_ignored=False) -> bool:
    """Called when the concerned Key is of str type to see if it matched with the given key path.

    :param key: Key string to be matched with 3 forms: 'name', '>root>branch>leaf' or 'grandpa>parent>child'
    :param key_path: The key path used to get the right keys, shall be in form of '>key1', '>k1>k2' and etc.
    :param case_ignored: True for case in-sensitive comparison, False for case sensitive.
    :return: True if the given Key string or Pattern matched with the key path, otherwise False in several cases:
        1) key of 'name': denotes only the name of the key-value-pair -> only the last segment of key_path would
            be compared align with the case_ignored flag;
        2) key of full path '>root>branch>leaf': defines a full path thus compare all of key_path.
        3) key of partial path 'p>child': to match multiple cases like ">root1>p>child' & '>root2>gpa>p>child'
    """
    if DeepDelta.PATH_SEPARATOR not in key:
        last_key = key_path.split(DeepDelta.PATH_SEPARATOR)[-1]
        return key.casefold() == last_key.casefold() \
            if case_ignored \
            else key == last_key
    elif key[0] == DeepDelta.PATH_SEPARATOR:
        return key.casefold() == key_path.casefold() \
            if case_ignored \
            else key == key_path
    else:
        return key_path.casefold().endswith(key.casefold()) \
            if case_ignored \
            else key_path.endswith(key)


def matched_keys(key_path: Any, all_keys: Sequence, case_ignored: bool, space_trimmed: bool = False) -> List:
    """With a given key_path, choose all matched keys with case_ignored and space_trimmed applied from the all_keys.

    :param key_path: the concerned key in forms like '>root>parent>name' or '>name'
    :param all_keys: the scope of keys that shall be either str or re.Pattern.
    :param case_ignored: True for case in-sensitive comparison, False for case sensitive.
    :param space_trimmed: Trim the leading&ending spaces if True, otherwise False.
    :return: list of all keys of the all_keys matched with the given key_path.
    """
    normalized = normalize(key_path, case_ignored, space_trimmed)
    keys = [k for k in all_keys if key_matches(k, normalized, case_ignored)]

    if len(keys) > 1:
        logger.warning(f"Multiple matching of '{key_path}': {','.join((str(k) for k in keys))}")
    return keys


@singledispatch
def normalize(key, case_ignored: bool = False, space_trimmed: bool = False) -> str:
    """Normalize a key to a string with optional case_ignored or space_trimmed.

    :param key: the key to be normalized, can be any type
    :param case_ignored: True for case in-sensitive comparison, False for case sensitive.
    :param space_trimmed: Trim the leading&ending spaces if True, otherwise False.
    :return: str(key) by default with case_ignored and space_trimmed applied.
    """
    return normalize(str(key), case_ignored, space_trimmed)


@normalize.register(tuple)
def _(tpl: Tuple, case_ignored: bool = False, space_trimmed: bool = False) -> Tuple:
    """Normalize a tuple with optional case_ignored or space_trimmed.

    :param tpl: the key of tuple type.
    :param case_ignored: True for case in-sensitive comparison, False for case sensitive.
    :param space_trimmed: Trim the leading&ending spaces if True, otherwise False.
    :return: str(key) by default with case_ignored and space_trimmed applied.
    """
    return tuple(normalize(item, case_ignored, space_trimmed) for item in tpl)


@normalize.register(str)
def _(str_key: str, case_ignored: bool = False, space_trimmed: bool = False) -> str:
    """Normalize a string with optional case_ignored or space_trimmed.

    :param str_key: the key of str type.
    :param case_ignored: True for case in-sensitive comparison, False for case sensitive.
    :param space_trimmed: Trim the leading&ending spaces if True, otherwise False.
    :return: str(key) by default with case_ignored and space_trimmed applied.
    """
    cased_key = str_key.casefold() if case_ignored else str_key
    return cased_key.strip() if space_trimmed else cased_key


@normalize.register(date)
@normalize.register(datetime)
def _(date_key, case_ignored: bool = False, space_trimmed: bool = False) -> str:
    """Normalize a key of date or datetime type with format of DeepDelta.DEFAULT_DATE_FORMAT,
    then change case or strip as instructed.

    :param date_key: the key of date or datetime type.
    :param case_ignored: True for case in-sensitive comparison, False for case sensitive.
    :param space_trimmed: Trim the leading&ending spaces if True, otherwise False.
    :return: str(key) by default with case_ignored and space_trimmed applied.
    """
    str_key = date_key.strftime(DeepDelta.DEFAULT_DATE_FORMAT)
    return normalize(str_key, case_ignored, space_trimmed)


@normalize.register(float)
@normalize.register(Decimal)
def _(float_key, case_ignored: bool = False, space_trimmed: bool = False) -> str:
    """Normalize a float number to string with fixed digits left.

    :param date_key: the key of date or datetime type.
    :param case_ignored: True for case in-sensitive comparison, False for case sensitive.
    :param space_trimmed: Trim the leading&ending spaces if True, otherwise False.
    :return: str(key) by default with case_ignored and space_trimmed applied.
    """
    return f"{{:.{DeepDelta.DEFAULT_FLOAT_NUMBER_DIGITS}f}}".format(float_key)


def key_denoted_by_id(name: Any, case_ignored: bool = False) -> bool:
    """ Help method to predicate if the given name is a key by checking if it ends or starts with 'id'.

    :param name: the key or property name to be evaluated.
    :param case_ignored: True for case in-sensitive comparison, False for case sensitive.
    :return: True if the given name starts/ends with 'id', otherwise False.
    """
    name_str = normalize(name, case_ignored, True)
    return name_str.endswith('id') or name_str.startswith('id')


def get_matched_keys(candidates: set, is_key: Callable = None, case_ignored: bool = True, *keys: List) -> Set:
    """Filter with predicate or known keys to get the matched keys from the candidates in sequence below:
    1) If keys are given, then find them from the candidates with case_ignored flag and trim the spaces.
    2) Or if the predicate is specified, evaluate the candidates to get the matched ones.
    3) Otherwise return empty set.

    :param candidates: the candidates to be evaluated like all keys of a dictionary.
    :param is_key: predicate to evaluate if any candidate is qualified as a key.
    :param case_ignored: True for case in-sensitive comparison, False for case sensitive.
    :param keys: known keys if specified.
    :return: all qualified keys from the given candidates as a set.
    """
    if keys:
        matched = {k for k in candidates if matched_keys(k, keys, case_ignored, True)}
    elif is_key:
        matched = {k for k in candidates if is_key(k, case_ignored)}
    else:
        matched = set()
    return matched


def guess_keys(seq: Sequence, is_key: Callable = None, case_ignored: bool = True, *keys: List[Any]) -> Set:
    """For a given sequence of the same type, try to guess their shared keys.

    :param seq: Sequence composed by either dict or instances of the same class.
    :param is_key: predicate to test if a name is key.
    :param case_ignored: True for case in-sensitive comparison, False for case sensitive.
    :param keys: list of keys specified explicitly.
    :return: Set of keys shared by all members of the given sequence.
    """
    if not seq:
        # empty sequence: return whatever set
        return set(keys)
    items = list(seq)
    item_types = {type(item) for item in items}
    if len(item_types) != 1:
        return {}
        # raise TypeError(f"Sequence with different items of {','.join(item_types)} is not supported.")

    item_type = item_types.pop()
    if issubclass(item_type, Mapping):
        key_sets = [set(item.keys()) for item in items]
        shared_keys = set.intersection(*key_sets)
    else: # if hasattr(item_type, '__dict__'):
        if len(items) > 0 and hasattr(items[0], '__dict__'):
            key_sets = [set(item.__dict__.keys()) for item in items]
            shared_keys = set.intersection(*key_sets)
        else:
            shared_keys = {}

    # else:
    #     d = {i: items[i] for i in range(0, len(items))}
    #     shared_keys = d.keys()

    return get_matched_keys(shared_keys, is_key, case_ignored, *keys)


def sequence_to_dict(seq: Sequence, is_key: Callable = None, case_ignored: bool = True, *keys: List[Any]) -> Dict:
    """Convert the given sequence of either dict or instances of same class to a dict by extract their keys.

    :param seq: Sequence composed by either dict or instances of the same class.
    :param is_key: predicate to test if a name is key.
    :param case_ignored: True for case in-sensitive comparison, False for case sensitive.
    :param keys: list of keys specified explicitly.
    :return: a dict with keys extracted from the items of the sequence.
    """

    keys = list(guess_keys(seq, is_key, case_ignored, *keys))
    items = list(seq)
    item_type = type(items[0])
    if len(keys) == 0:
        return {str(i): items[i] for i in range(len(items))}
    elif len(keys) == 1:
        if issubclass(item_type, Mapping):
            return {item[keys[0]]: item for item in items}
        else:
            return {item.__dict__[keys[0]]: vars(item) for item in items}
    else:
        keys.sort()
        if issubclass(item_type, Mapping):
            return {tuple(item[k] for k in keys): item for item in items}
        else:
            return {tuple(item.__dict__[k] for k in keys): vars(item) for item in items}


class DeepDelta:
    """ Core class to embed DeltaConfig, DeltaOutput to perform deep comparison of any two objects.

    """

    PATH_SEPARATOR = '>'
    MISSING = 'MISSING'
    DEFAULT_DATE_FORMAT = '%Y-%b-%d'
    DEFAULT_FLOAT_NUMBER_DIGITS = 2

    def __init__(self,
                 config: DeltaConfig = None,
                 type_comparators: Dict[Union[Tuple[Type, Type], Type], Callable[[Any, Any], bool]] = None,
                 named_comparators: Dict[str, Callable[[Any, Any, str], Any]] = None,
                 *excluded_keys: List[Union[str, Pattern]]):
        """Initialize the DeepDelta instance with both various settings and comparators.

        :param config: the DeltaConfig instance specifying behaviours of the DeepDelta instance including:
            - Case sensitivity of keys and/or values
            - If spaces of keys and/or values shall be trimmed
            - Should keys ended/started with 'id' shall be treated as unique key to convert sequences to dicts
            - If default values (0, '', False, [] and ect.) can be treated as equal to None
            - If missing keys can be treated as whose values to be Nones
            - Output rules with pre-defined means to show the comparison result, the None/tuples is used by default
        :param type_comparators: enable values of different types to be compared, copy of the DEFAULT_TYPE_COMPARATOR
            would be used if None is specified.
        :param named_comparators: enable dedicated comparators against specific keys or patterns to get deltas directly.
        :param excluded_keys: list of keys to be excluded from comparison
        """
        self._config: DeltaConfig = config or DEFAULT_DELTA_CONFIG
        self.output:  Callable[[bool, Any, Any], Any] = get_output(self._config)
        none_unequal_default: bool = self._config.matches(DeltaConfig.NoneUnequalDefault)
        self.typed_equal: Callable[[Any, Any], bool] = with_comparators(type_comparators, none_unequal_default)
        self.named_comparators = named_comparators or {}
        self.keys_excluded: List[Union[str, Pattern]] = list(excluded_keys)

    def as_delta(self, as_dif: bool, lhs: Any, rhs: Any) -> Tuple:
        """Use the output rules&means defined in Output_Buffer of delta_output.py to summarize the comparison results.

        :param as_dif: boolean to indicate if the lhs and rhs shall be treated as different.
        :param lhs: left-hand side value under comparison
        :param rhs: right-hand side value under comparison
        :return: depending on the flags of the DeltaConfig initializing this DeepDelta, tuple/dict/str to show if and
            how the delta is between lhs and rhs. By default: None if no difference, (lhs, rhs) if lhs is not regarded
            as equal to rhs.
        """
        return self.output(as_dif, lhs, rhs)

    def get_named_comparator(self, key_path: str):
        """ Get the dedicated comparator for a given key_path to compare value pairs under the matched names.

        The comparator defined shall accept 3 input arguments (lhs, rhs, key_path) to get a boolean output:
            True if lhs is regarded as different than rhs, otherwise False.
        :param key_path: the string representation of the current key to be compared, like '>key' or '>key1>sub_key2'.
        :return: the FIRST matched comparator if the given key_path matching any str/pattern of the named comparator
            dictionary, otherwise None.
        """
        case_ignored = self._config.matches(DeltaConfig.KeyCaseIgnored)
        for k in self.named_comparators:
            if key_matches(k, key_path, case_ignored):
                return self.named_comparators[k]
        return None

    def is_excluded(self, key_path: str) -> bool:
        """Check if the given key shall be excluded from comparisons when it is defined as either str or pattern in
        advance in __init__().

        :param key_path: the string representation of the current key to be compared, like '>key' or '>key1>sub_key2'.
        :return: True if the key_path shall be excluded explicitly, otherwise False.
        """
        case_ignored = self._config.matches(DeltaConfig.KeyCaseIgnored)
        for k in self.keys_excluded:
            if key_matches(k, key_path, case_ignored):
                return True
        return False

    def compare_any(self, lhs: Any, rhs: Any, key_path: str = None) -> Union[None, Tuple, Dict, str]:
        """Compare any two values to see if they are different, then format it by calling self.as_delta().

        The comparison between lhs and rhs would happen in following order:
         1) named comparators Callable[[Any, Any, str], bool] would be used if comparator of the key is specified.
         2) compare lhs and rhs with Python default equals and accept the fact if they are identical.
         3) handle case-sensitivity-enabled and space-trim-enabled comparison if both lhs and rhs are strings.
         4) compare two dictionaries by calling self.compare_dict()
         5) compare two sequences by calling self.compare_sequence() which would try to convert sequences to dicts.
         6) use the given or default typed comparators if possible to compare them.
         7) finally, regard lhs is different than rhs if no typed comparators found.

        :param lhs: left-hand side value under comparison
        :param rhs: right-hand side value under comparison
        :param key_path: the string representation of the current key to be compared, like '>key' or '>key1>sub_key2'.
        :return: the tuple/dict/str to show if and how the delta is between lhs and rhs.
            By default: None if no difference, (lhs, rhs) if lhs is not regarded as equal to rhs.
        """
        named_comparator = self.get_named_comparator(key_path := key_path or '')
        if named_comparator:
            return self.as_delta(named_comparator(lhs, rhs, key_path), lhs, rhs)
        elif lhs == rhs:
            return self.as_delta(False, lhs, rhs)

        value_space_trimmed = self._config.matches(DeltaConfig.ValueSpaceTrimmed)
        if isinstance(lhs, str) and isinstance(rhs, str):
            if value_case_ignored := self._config.matches(DeltaConfig.ValueCaseIgnored):
                is_dif = ((lhs.strip().casefold() != rhs.strip().casefold())
                          if value_space_trimmed else (lhs.casefold() != rhs.casefold()))
            else:
                is_dif = (lhs.strip() != rhs.strip()
                          if value_space_trimmed else (lhs != rhs))
            return self.as_delta(is_dif, lhs, rhs)
        if isinstance(lhs, Mapping) and isinstance(rhs, Mapping):
            return self.compare_dict(lhs, rhs, key_path)
        elif isinstance(lhs, Sequence) and isinstance(rhs, Sequence):
            return self.compare_sequence(lhs, rhs, key_path)

        typed_result = self.typed_equal(lhs, rhs)
        if isinstance(typed_result, bool):
            return self.as_delta(not typed_result, lhs, rhs)

        return self.as_delta(True, lhs, rhs)

    def compare_dict(self, lhs: Mapping, rhs: Mapping, dict_path: str) -> Union[None, Tuple, Dict, str]:
        """ Compare two dictionaries to see if they are different, then format it by calling self.as_delta().

        :param lhs: left-hand side dict under comparison
        :param rhs: right-hand side dict under comparison
        :param dict_path: the string representation of the current key to be compared, like '>key' or '>key1>sub_key2'.
        :return: the tuple/dict/str to show if and how the delta is between lhs and rhs.
            By default: None if no difference, (lhs, rhs) if lhs is not regarded as equal to rhs.
        """
        case_ignored = self._config.matches(DeltaConfig.KeyCaseIgnored)
        key_space_trimmed = self._config.matches(DeltaConfig.KeySpaceTrimmed)
        missing_as_none = self._config.matches(DeltaConfig.MissingAsNone)

        # Duplicated keys under CaseIgnored/TrimSpace settings would be warned only,
        l_keys = {k for k in lhs.keys() if not self.is_excluded(f'{dict_path}{DeepDelta.PATH_SEPARATOR}{k}')}
        r_keys = {k for k in rhs.keys() if not self.is_excluded(f'{dict_path}{DeepDelta.PATH_SEPARATOR}{k}')}
        all_keys = {normalize(k, case_ignored) for k in l_keys.union(r_keys)}
        delta = {}
        for key in all_keys:
            key_path = f'{dict_path}{DeepDelta.PATH_SEPARATOR}{key}'
            if self.is_excluded(key_path):
                continue

            lks = matched_keys(key, l_keys, case_ignored, key_space_trimmed)
            rks = matched_keys(key, r_keys, case_ignored, key_space_trimmed)
            # value of the last matched key would be used for comparison
            l_value = lhs[lks[-1]] if len(lks)>0 else (None if missing_as_none else DeepDelta.MISSING)
            r_value = rhs[rks[-1]] if len(rks)>0 else (None if missing_as_none else DeepDelta.MISSING)
            named_comparator = self.get_named_comparator(key_path)
            if named_comparator:
                delta[key] = named_comparator(l_value, r_value, key_path)
            elif l_value == r_value:
                delta[key] = self.as_delta(False, l_value, r_value)
            else:
                delta[key] = self.compare_any(l_value, r_value, key_path)

        result = {k: v for k, v in delta.items() if self.delta_to_keep(v)}
        return result

    def delta_to_keep(self, value: Any):
        """ Help method to check if the deltas shall be kept for reporting purposes.

        Depending on the DeltaConfig used to initialize this DeepDelta:
        1) if OutputKeepAllDetails is set, then all details used for comparisons would be kept.
        2) discard Nones.
        3) discard any sequence that is empty.
        4) depends on Python embed conversion to boolean.

        :param value: the delta value could be discarded.
        :return: True to reserve the value, False to discard.
        """
        if self._config.matches(DeltaConfig.OutputKeepAllDetails):
            return True
        elif value is None:
            return False
        elif self._config.matches(DeltaConfig.OutputWithFlag) and isinstance(value, tuple):
            return value[0]
        elif isinstance(value, Collection):
            return len(value) != 0

        return value

    def compare_sequence(self, lhs: Sequence, rhs: Sequence,
                         seq_path: str = None,
                         is_key: Callable[[Any, bool], bool] = None,
                         *keys: List[Any]) -> Union[None, Tuple, Dict, str]:
        """ Compare two sequences to see if they are different, then format it by calling self.as_delta().

        :param lhs: left-hand side sequence under comparison
        :param rhs: right-hand side sequence under comparison
        :param seq_path: the string representation of the current key to be compared, like '>key' or '>key1>sub_key2'.
        :param is_key: predicate to check if the name or property of the sequences shall be used as key.
        :param keys: keys specified explicitly.
        :return: the tuple/dict/str to show if and how the delta is between lhs and rhs.
            By default: None if no difference, (lhs, rhs) if lhs is not regarded as equal to rhs.
        """
        seq_path = seq_path or ''
        case_ignored = self._config.matches(DeltaConfig.KeyCaseIgnored)
        
        is_key = is_key or (key_denoted_by_id if self._config.matches(DeltaConfig.IdAsKey) else None)
        l_keys = guess_keys(lhs, is_key, case_ignored, *keys)
        r_keys = guess_keys(rhs, is_key, case_ignored, *keys)
        keys = l_keys.intersection(r_keys)
        l_dict = sequence_to_dict(lhs, is_key, case_ignored, *keys)
        r_dict = sequence_to_dict(rhs, is_key, case_ignored, *keys)
        return self.compare_dict(l_dict, r_dict, seq_path)

    @staticmethod
    def convert_to_compare(lhs: Sequence, rhs: Sequence,
                           comparator: DeepDelta = None,
                           is_key: Callable = None,
                           *keys: List[Any]) -> Union[None, Tuple, Dict, str]:
        """ Convert two sequences to dicts with the optional is_key predicate or keys, then compare them with the
            optional DeepDelta instance.

        :param lhs: left-hand side sequence under comparison
        :param rhs: right-hand side sequence under comparison
        :param comparator: the optional DeepDelta instance to be used to compare the converted dicts.
        :param is_key: predicate to check if the name or property of the sequences shall be used as key.
        :param keys: keys specified explicitly.
        :return: the tuple/dict/str/None of the comparison output by the comparator.
        """
        comparator = comparator or DeepDelta()
        return comparator.compare_sequence(lhs, rhs, '', is_key, *keys)

    @staticmethod
    def compare(lhs: Any, rhs: Any,
                options: DeltaConfig = None,
                type_comparators: Dict[Union[Tuple[Type, Type], Type], Callable[[Any, Any], bool]] = None,
                named_comparators: Dict[str, Callable[[Any, Any], bool]] = None,
                *excluded_keys: List[Union[str, Pattern]]) -> Union[None, Tuple, Dict, str]:
        """ Entrance method to construct a new DeepDelta instance to compare two values.

        :param lhs: left-hand side value under comparison
        :param rhs: right-hand side value under comparison
        :param options: the DeltaConfig instance specifying behaviours of the DeepDelta instance including:
            - Case sensitivity of keys and/or values
            - If spaces of keys and/or values shall be trimmed
            - Should keys ended/started with 'id' shall be treated as unique key to convert sequences to dicts
            - If default values (0, '', False, [] and ect.) can be treated as equal to None
            - If missing keys can be treated as whose values to be Nones
            - Output rules with pre-defined means to show the comparison result, the None/tuples is used by default
        :param type_comparators: enable values of different types to be compared, copy of the DEFAULT_TYPE_COMPARATOR
            would be used if None is specified.
        :param named_comparators: enable dedicated comparators against specific keys or patterns.
        :param excluded_keys: list of keys to be excluded from comparison
        :return: the tuple/dict/str to show if and how the delta is between lhs and rhs.
            By default: None if no difference, (lhs, rhs) if lhs is not regarded as equal to rhs.
        """
        comparator = DeepDelta(options, type_comparators, named_comparators, *excluded_keys)
        return comparator.compare_any(lhs, rhs)

