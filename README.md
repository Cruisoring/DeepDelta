# DeepDelta

## Overview

DeepDelta is a compact Python library to compare any two objects with a rich set of configurable options and comparators with any desirable output format.


## Installation

Install from PyPi:

`>pip install deepdelta`


## How to use

The main function to be called is ![DeepDelta.compare()|](https://github.com/Cruisoring/DeepDelta/blob/master/deepdelta/core.py):
```
def compare(lhs: Any, rhs: Any,
             options: DeltaConfig = None,
             type_comparators: Dict[Union[Tuple[Type, Type], Type], Callable[[Any, Any], bool]] = None,
             named_comparators: Dict[str, Callable[[Any, Any], bool]] = None,
             *excluded_keys: List[Union[str, Pattern]]) -> Union[None, Tuple, Dict, str]
```
                
There are 4 optional parameters in addition to the 2 data to be compared:
1. **options** of type [DeltaConfig](https://github.com/Cruisoring/DeepDelta/blob/master/deepdelta/delta_config.py): Flag/Enum based settings to specify how comparison to be performed.
2. **type_comparators** of type *Dict[Union[Tuple[Type, Type], Type], Callable[[Any, Any], bool]]*: specifies how values of different types shall be compared.
3. **named_comparators** of type *Dict[str, Callable[[Any, Any], bool]]*: defines how values with specific names would be compared with customised comparator.
4. **excluded_keys** of type *List[Union[str, Pattern]]*: keys to be excluded from comparison if their path matched by either str or Pattern.

The output of comparing two values would be None/Tuple/Dict/str as specified by the flags of `0b11111 << 7`: None means no reportable difference found if presented.

### Set comparison preferences

The optional [DeltaConfig](https://github.com/Cruisoring/DeepDelta/blob/master/deepdelta/delta_config.py) defines how DeepDelta would behave with options of:
- Case sensitivity of keys and/or values
- If spaces of keys and/or values shall be trimmed
- Should keys ended/started with 'id' shall be treated as unique key to convert sequences to dicts
- If default values (0, '', False, [] and ect.) can be treated as equal to None
- If missing keys can be treated as whose values to be Nones
- Output rules with pre-defined means to show the comparison result, the None/tuples is used by default

If it is not specified, then the DEFAULT_DELTA_CONFIG defined in [core.py](https://github.com/Cruisoring/DeepDelta/blob/master/deepdelta/core.py) as:
```
DEFAULT_DELTA_CONFIG: DeltaConfig = DeltaConfig.CaseIgnored\
                                    | DeltaConfig.SpaceTrimmed\
                                    | DeltaConfig.IdAsKey \
                                    | DeltaConfig.MissingAsNone \
                                    | DeltaConfig.OutputDefault
```
Thus the DeepDelta would compare two values by:
1) Ignore cases of key and value
2) Trim spaces of keys before comparison
3) Try to use the IDs as keys to convert list to dict
4) Missing of a key is treated as if its value is defined as None
5) Output in default format: Deltas as tuples of (left_value, right_value) if values are different, otherwise None    

There are many examples of how it works in [test_deep_delta.py](https://github.com/Cruisoring/DeepDelta/blob/master/tests/test_deep_delta.py).

### Compare values of different types

When comparing Python objects with their deserialized formats like JSON files, instead of convert the picked values back to their original types, like *str* back to *datetime*/*float*/*bool*, making *str* comparable with these Python build-in types would save us quite some boiler-plate codes.

This is enabled with the optional **type_comparators** argument to initialize the **DeepDelta** with values of function/lambda to compare the two values.
 
You can define any type based comparator in two ways:
1) The tuple of two types of the value to compare as the key. Like *(int, datetime)* as the key, then the associated function/lambda would be used to compare a *int* with a *datetime*, or a *datetime* with an *int*.
2) The type of one value to be compared as the key. Hopefully you don't need it when there could be potential conflictions with other entries.

The [comparator.py](https://github.com/Cruisoring/DeepDelta/blob/master/deepdelta/comparator.py) has defined a common set of methods like:
- compare two values of *float*/*int*/*Decimal*/*str* types as two float point numbers with optional digits to compare.
- treat dedicated values (*{True, 'True', 'Yes', 'Y', 'Positive', 1, 'TRUE', 'yes'}*  as boolean **True** by default) as **True** and **False** that could be appended/modified with the static variables **TRUE_VALUES** and **FALSE_VALUES** of the [comparator.py](https://github.com/Cruisoring/DeepDelta/blob/master/deepdelta/comparator.py).
- compare str with *datetime* by convert it to *datetime* by trying a set of formats of **DATETIME_FORMATS** in the [comparator.py](https://github.com/Cruisoring/DeepDelta/blob/master/deepdelta/comparator.py) that is also modifiable.
_ treat **None** equal to Python default values (like 0, False, [] and etc.) when **DeltaConfig.NoneUnequalDefault** is set.

If the **type_comparators** argument is not set, then the **DEFAULT_TYPE_COMPARATOR: Dict[Union[Tuple[Type, Type], Type], Callable[[Any, Any], bool]]** defined in the [comparator.py](https://github.com/Cruisoring/DeepDelta/blob/master/deepdelta/comparator.py) would be used as a blue-print to enable inter-types comparisons between common values.

### Compare values of specific names

The **named_comparators** argument in above *compare()* method means to enable most specific comparisons on targeted keys/fields of the two objects under comparison.

The sample below shows how it works:
```
def test_named_comparator():
    comparators = DeepDelta(DEFAULT_DELTA_CONFIG ^ DeltaConfig.ValueCaseIgnored)
    compare_p = lambda l, r, p: DeepDelta.convert_to_compare(l, r, comparators, lambda n, case_ignored: 'no' in n)
    named = {
        'Id': lambda l, r, p: None if l==r or l+r==0 else (l, r),
        'products': compare_p,
        'Purchased': lambda l, r, p: None if Comparator.compare_as_datetime_values(l, r) else (l, r)}
    order1 = {'id': 100, 'purchased': '2020 Aug 6', 'products': products1}
    order2 = {'ID': -100, 'PURCHASED': '6/Aug/2020', 'PRODUCTS': products2}
    delta = DeepDelta.compare(order1, order2, None, None, named)
    assert delta == {'products': {'1202': {'description': ('Subway', 'SUBWAY')},
                                  '2009': {'description': ('Hochy', 'Hochey'),
                                           'name': ('wipes', 'Wipes')},
                                  '5001': {'unit': ('per', 'piece')}}}
``` 

The keys in above example ('Id', 'products', 'Purchased') would be matched case-ignored with the actual keys in the two values *order1* and *order2*. It is also possible to define more complex key patterns to match multiple fields/keys to compare with shared logic.

### Exclude fields/keys

The **excluded_keys** arguments specified any keys/key_paths to be neglected during the comparison process.

### Compare two lists

For normal Python class instances, the **vars()** would be called to get their variables as dicts.

A key idea of comparing two lists of similar objects is that both list would be converted to dicts, then the objects sharing the same/similar keys would be compared side by side.

The other static method DeepDelta.convert_to_compare() is defined as: 
```
    def convert_to_compare(lhs: Sequence, rhs: Sequence,
                           comparator: DeepDelta = None,
                           is_key: Callable = None,
                           *keys: List[Any]) -> Union[None, Tuple, Dict, str]:
```

The above **comparator** allows you to specify all configurable settings as compare any generic values. The *keys* can be used to denote keys of both *lhs* and *rhs* directly. Alternatively, the predicate *is_key* would detect all concerned keys or detect any keys starts or ends with 'id'.

The key part of the test shows how it works to compare two lists of *Product* instances:
```
def test_convert_to_compare():
    delta = DeepDelta.convert_to_compare(products1, products2, None, lambda name, case_ignored: 'no' in name)
    assert delta == { '2009': {'description': ('Hochy', 'Hochey')},
        '5001': {'unit': ('per', 'piece')}}

    comparators = DeepDelta(DEFAULT_DELTA_CONFIG ^ DeltaConfig.ValueCaseIgnored)
    delta = DeepDelta.convert_to_compare(products1, products2, comparators, lambda name, case_ignored: 'no' in name)
    assert delta == {'1202': {'description': ('Subway', 'SUBWAY')},
                     '2009': {'description': ('Hochy', 'Hochey'), 'name': ('wipes', 'Wipes')},
                     '5001': {'unit': ('per', 'piece')}}
```

## Summary

The DeepDelta can be used to compare two objects by calling the static *DeelDelta.compare(lhs, rhs)* directly, with many default functions, to get a decent outcome with deltas highlighted.

For advanced comparison scenarios, the Functional Programming design makes it possible to define and enforce complex logics upon concerned types or keys directly.

 
