import re
from datetime import datetime
from pprint import pprint

from comparator import Comparator, with_precision
from core import DeepDelta, DEFAULT_DELTA_CONFIG
from delta_config import DeltaConfig
from delta_output import Output_Buffer


class Employee:
    def __init__(self, dId, dep, eId, name, gender):
        self.departmentId = dId
        self.department = dep
        self.employeeId = eId
        self.name = name
        self.gender = gender


named_comparators = {
    'date': Comparator.compare_as_datetime_values,
    'total': with_precision(3)
}

default_comparator = DeepDelta(None, None, named_comparators, 'abc', 'ef')

employees = [
    Employee(1, 'Sales', 123, 'Ali', 'male'),
    Employee(2, 'IT', 235, 'Tom', 'male'),
    Employee(1, 'Sales', 135, 'Linda', 'female'),
    Employee(1, 'Sales', 178, 'Clair', 'female'),
    Employee(3, 'Support', 326, 'Bruce', 'male'),
    Employee(3, 'Support', 377, 'Ben', 'male'),
    Employee(1, 'Sales', 138, 'Frank', 'male'),
]


dict_list = [
    {'departmentId': 1, 'department': 'Sales', 'employeeId': 123, 'name': 'Ali', 'gender': 'male'},
    {'departmentId': 2, 'department': 'IT', 'employeeId': 235, 'name': 'Tom', 'gender': 'male'},
    {'departmentId': 1, 'department': 'Sales', 'employeeId': 135, 'name': 'Blinder', 'gender': 'female'},
    {'departmentId': 1, 'department': 'Sales', 'employeeId': 178, 'name': 'Clair', 'gender': 'female'},
    {'departmentId': 3, 'department': 'Unknown', 'employeeId': 326, 'name': 'Bruce', 'gender': 'male'},
    {'departmentId': 3, 'department': 'Support', 'employeeId': 377, 'name': 'Ben', 'gender': 'male'},
    {'departmentId': 1, 'department': 'Sales', 'employeeId': 138, 'name': 'Frank', 'gender': 'male'},
]


dict_list2 = [
    {'departmentId': 1, 'department': 'Sales', 'employeeId': 178, 'name': 'Clair', 'gender': 'female'},
    {'departmentId': 3, 'department': 'support', 'employeeId': 377, 'name': 'Ben', 'gender': 'male'},
    {'departmentId': 2, 'department': 'IT', 'employeeId': 235, 'name': 'Tommy', 'gender': 'male'},
    {'departmentId': 1, 'department': 'Sales', 'employeeId': 123, 'name': 'Ali', 'gender': 'male'},
    {'departmentId': 1, 'department': 'Sales', 'employeeId': 135, 'name': 'Blinder', 'gender': 'female'},
    {'departmentId': 1, 'department': 'sales', 'employeeId': 138, 'name': 'Frank', 'gender': 'male'},
    {'departmentId': 3, 'department': 'Manage', 'employeeId': 327, 'name': 'Harry', 'gender': 'male'},
]


def test_default_options():
    assert default_comparator._config == DEFAULT_DELTA_CONFIG


def test_compare_simple_values_of_same_types():
    assert default_comparator.compare_any(2.77, 3.22) == (2.77, 3.22)
    assert default_comparator.compare_any(2.77, 2.77) is None
    assert default_comparator.compare_any(True, True) is None
    assert default_comparator.compare_any(False, True) == (False, True)


def test_compare_simple_values_of_defined_types():
    assert default_comparator.compare_any(2.77, 3.22) == (2.77, 3.22)
    assert default_comparator.compare_any(2.77, 2.77) is None
    assert default_comparator.compare_any(True, True) is None
    assert default_comparator.compare_any(False, True) == (False, True)


def test_default_compare_two_lists_as_similar_dicts():
    result = default_comparator.compare_any(employees, dict_list)
    pprint(result)
    result = default_comparator.compare_any(dict_list, dict_list2)
    pprint(result)
    assert ('Tom', 'Tommy') == result[('2', '235')]['name']


def test_compare_with_options_case_ignored():
    result = default_comparator.compare(dict_list, dict_list2, DeltaConfig.CaseIgnored | DeltaConfig.IdAsKey)
    pprint(result)
    assert len(result) == 3


def test_compare_with_options_dif_outputs():
    for option in Output_Buffer.keys():
        result = DeepDelta.compare(dict_list, dict_list2, option)
        pprint(f'{option}:\n{result}')


shopping_list = [
    {'name': 'bread', 'expired': datetime(2010, 10, 7), 'price': 2.98, 'brand': 'SoftLake', 'amount': 2},
    {'name': 'milk', 'expired': datetime(2010, 10, 8), 'price': 4, 'brand': 'DiaryFarm', 'amount': 1},
]

basket = [
    {'Name': 'BREAD', 'Expired': '2010-10-07', 'price': '2.99', 'brand': 'SOFTLake', 'amount': '2.000003'},
    {'Name': 'MILK', 'Expired': '2010 Oct 9', 'price': '3.98', 'brand': 'DiaryFarm', 'amount': '1'},
]


def test_compare_with_default_settings():
    result = DeepDelta.compare(shopping_list, basket, DeltaConfig.KeyCaseIgnored)
    pprint(result)
    assert set(result['0'].keys()) == {'brand', 'name', 'price'} and set(result['1'].keys()) == {'name', 'expired'}

    result = DeepDelta.compare(shopping_list, basket,
                               DeltaConfig.CaseIgnored)
    pprint(result)
    assert set(result['0'].keys()) == {'price'} and set(result['1'].keys()) == {'expired'}


def test_compare_with_exclusive_key_strings():
    result = DeepDelta.compare(shopping_list, basket, DeltaConfig.KeyCaseIgnored, None, None, 'BRAND', 'PRICE')
    pprint(result)
    assert set(result['0'].keys()) == {'name'} and set(result['1'].keys()) == {'name', 'expired'}


def test_compare_with_exclusive_key_patterns():
    result = DeepDelta.compare(shopping_list, basket, DeltaConfig.KeyCaseIgnored, None, None,
                               re.compile(r'>0>.*[ce|me]'), re.compile('>1.*ex.+'))
    pprint(result)
    assert set(result['0'].keys()) == {'brand'} and set(result['1'].keys()) == {'name'}


def test_compare_with_named_comparator():
    named = {
        'price': lambda l, r, p: float(l) >= float(r),
        re.compile('>0.*brand'): lambda l, r, p: str(l).casefold() != str(r).casefold(),
    }
    result = DeepDelta.compare(shopping_list, basket, DeltaConfig.KeyCaseIgnored, None, named)
    pprint(result)
    assert set(result['0'].keys()) == {'name'} and set(result['1'].keys()) == {'name', 'expired', 'price'}
    result = DeepDelta.compare(basket, shopping_list, DeltaConfig.KeyCaseIgnored, None, named)
    pprint(result)
    assert set(result['0'].keys()) == {'name', 'price'} and set(result['1'].keys()) == {'name', 'expired'}


def test_none_unequal_default():
    default_dict = {
        'int': 0, 'str': '', 'float': 0.0, 'bool': False,
        'list': [], 'set': set(), 'dict': {}}
    none_dict = {
        'int': None, 'str': None, 'float': None, 'bool': None,
        'list': None, 'set': None, 'dict': None}
    delta = DeepDelta.compare(default_dict, none_dict)
    assert len(delta) == 0
    delta = DeepDelta.compare(default_dict, none_dict, DeltaConfig.NoneUnequalDefault)
    pprint(delta)
    assert  len(delta) == len(default_dict)
    delta = DeepDelta.compare(none_dict, default_dict, DeltaConfig.NoneUnequalDefault)
    pprint(delta)
    assert  len(delta) == len(default_dict)


def test_missing_as_none():
    d1 = {'key1': 123, 'key2': False, 'key3': None}
    d2 = {'KEY1': '123', 'KEY2': None}

    delta = DeepDelta.compare(d1, d2)
    pprint(delta)
    assert len(delta) == 0

    delta = DeepDelta.compare(d1, d2, DEFAULT_DELTA_CONFIG ^ DeltaConfig.MissingAsNone)
    pprint(delta)
    assert len(delta) == 1


class Product:
    def __init__(self, prod_no, category, name, desc, price, unit):
        self.prod_no = prod_no
        self.category = category
        self.name = name
        self.description = desc
        self.price = price
        self.unit = unit


products1 = [
    Product(1001, 'dairy', 'milk', 'Coles', 2.99, None),
    Product(1202, 'bakery', 'bread', 'Subway', 2, '$/loaf'),
    Product(2009, 'baby', 'wipes', 'Hochy', 5.50, '$/package'),
    Product(3023, 'beauty', 'shampoo', 'Noose', 8.50, '$/bottle'),
    Product(5001, 'fruit', 'apple', None, 0.99, 'per'),
]

products2 = (
    Product(1202, 'bakery', 'bread', 'SUBWAY', 2.2, '$/loaf'),
    Product(5001, 'fruit', 'apple', None, 0.99, 'piece'),
    Product(1001, 'dairy', 'milk', 'Coles', 2.99, None),
    Product(2009, 'baby', 'Wipes', 'Hochey', 5.50, '$/package'),
    Product(3023, 'beauty', 'shampoo', 'Noose', 8.50, '$/bottle'),
)


def test_convert_to_compare():
    delta = DeepDelta.convert_to_compare(products1, products2, None, lambda name, case_ignored: 'no' in name)
    assert delta == { '2009': {'description': ('Hochy', 'Hochey')},
        '5001': {'unit': ('per', 'piece')}}

    comparators = DeepDelta(DEFAULT_DELTA_CONFIG ^ DeltaConfig.ValueCaseIgnored)
    delta = DeepDelta.convert_to_compare(products1, products2, comparators, lambda name, case_ignored: 'no' in name)
    assert delta == {'1202': {'description': ('Subway', 'SUBWAY')},
                     '2009': {'description': ('Hochy', 'Hochey'), 'name': ('wipes', 'Wipes')},
                     '5001': {'unit': ('per', 'piece')}}


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
