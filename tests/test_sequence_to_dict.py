import logging

from deepdelta.core import guess_keys, sequence_to_dict, key_denoted_by_id

logger = logging.getLogger(__name__)

dict_list = [
    {'departmentId': 1, 'department': 'Sales', 'employeeId': 123, 'name': 'Ali', 'gender': 'male'},
    {'departmentId': 2, 'department': 'IT', 'employeeId': 235, 'name': 'Tom', 'gender': 'male'},
    {'departmentId': 1, 'department': 'Sales', 'employeeId': 135, 'name': 'Blinder', 'gender': 'female'},
    {'departmentId': 1, 'department': 'Sales', 'employeeId': 178, 'name': 'Clair', 'gender': 'female'},
    {'departmentId': 3, 'department': 'Support', 'employeeId': 326, 'name': 'Bruce', 'gender': 'male'},
    {'departmentId': 3, 'department': 'Support', 'employeeId': 377, 'name': 'Ben', 'gender': 'male'},
    {'departmentId': 1, 'department': 'Sales', 'employeeId': 138, 'name': 'Frank', 'gender': 'male'},
]


class Employee:
    def __init__(self, dId, dep, eId, name, gender):
        self.departmentId = dId
        self.department = dep
        self.employeeId = eId
        self.name = name
        self.gender = gender


employees = [
    Employee(1, 'Sales', 123, 'Ali', 'male'),
    Employee(2, 'IT', 235, 'Tom', 'male'),
    Employee(1, 'Sales', 135, 'Linda', 'female'),
    Employee(1, 'Sales', 178, 'Clair', 'female'),
    Employee(3, 'Support', 326, 'Bruce', 'male'),
    Employee(3, 'Support', 377, 'Ben', 'male'),
    Employee(1, 'Sales', 138, 'Frank', 'male'),
]


def test_guess_keys_by_default():
    keys = guess_keys(dict_list, key_denoted_by_id)
    keys2 = guess_keys(employees, key_denoted_by_id)
    logger.info(keys)
    assert len(keys) == 2
    assert keys2 == keys


def test_guess_keys_with_predicate():
    keys = guess_keys(dict_list, lambda name, case_ignored: name == 'employeeId', False)
    logger.info(keys)
    assert len(keys) == 1
    keys2 = guess_keys(employees, lambda name, case_ignored: name == 'employeeId', False)
    assert keys2 == keys


def test_guess_keys_with_keys_specified():
    keys = guess_keys(dict_list, None, False, 'name', 'employeeID')
    logger.info(keys)
    assert len(keys) == 1
    keys2 = guess_keys(employees, None, False, 'name', 'employeeID')
    assert keys2 == keys

    keys = guess_keys(dict_list, None, True, 'name', 'employeeID')
    logger.info(keys)
    assert len(keys) == 2
    keys2 = guess_keys(employees, None, True, 'name', 'employeeID')
    assert keys2 == keys


def test_dicts_to_dict():
    d = sequence_to_dict(dict_list, key_denoted_by_id, True, 'employeeid')
    assert 123 in d

    d = sequence_to_dict(dict_list, key_denoted_by_id)
    assert (1, 123) in d

    d = sequence_to_dict(employees, None, True, 'NAME')
    logger.info(d)
    assert 'Tom' in d

    d = sequence_to_dict(employees, lambda name, case_ignored: name.casefold() == 'employeeID'.casefold())
    logger.info(d)
    assert 123 in d

    d = sequence_to_dict(employees, lambda name, case_ignored: name == 'employeeID')
    assert '5' in d
