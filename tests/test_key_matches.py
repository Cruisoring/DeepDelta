import logging
import re

from deepdelta.core import key_matches, matched_keys, get_matched_keys, key_denoted_by_id

logger = logging.getLogger(__name__)


def test_key_matches_with_pattern():
    assert key_matches(re.compile(r'.*KEY\d+', re.I), '>key1', False) is True
    assert key_matches(re.compile('>key1 '), '>key1', False) is False
    assert key_matches(re.compile(r">.*>leaf", re.IGNORECASE), '>leaf', False) is False
    assert key_matches(re.compile(r">.*>leaf", re.IGNORECASE), '>any>LEAF', False) is True
    assert key_matches(re.compile(r".*key\d+>.*>leaf", re.IGNORECASE), '>KEY1>sub>leaF', False) is True


def test_key_matches_with_name():
    assert key_matches('key1', '>key1', False) is True
    assert key_matches('key1', '>Key1', False) is False
    assert key_matches('key1', '>abc>>key1', True) is True
    assert key_matches('key1', '>Key1', True) is True


def test_key_matches_with_full_path():
    assert key_matches('>key1', '>Key1', False) is False
    assert key_matches('>abc>leaf', '>abc>leaf', False) is True
    assert key_matches('>f>Leaf>more', '>More', False) is False
    assert key_matches('>f>Leaf>more', '>more', False) is False

    assert key_matches('>key1', '>root>key1', True) is False
    assert key_matches('>ABc>LEAF', '>abc>leaf', True) is True
    assert key_matches('>f>Leaf>more', '>f>leaf', True) is False


def test_key_matches_with_end_path():
    assert key_matches('abc>key1', '>abc>Key1', False) is False
    assert key_matches('abc>key1', '>abc>Key1', True) is True
    assert key_matches('>abc>leaf', '>abc>leaf', False) is True
    assert key_matches('leaf>more', '>f>Leaf>More', False) is False
    assert key_matches('F>more', '>f>Leaf>more', True) is True


test_dict = {
    'key1': "This is key1",
    ' Key1\n': "Shall not be matched with spaces",
    '>key1': "This is full-path key1",
    '>key1>sub>leaf': "Full path of a 3-levels key",
    'KEY1': "This is KEY1",
    re.compile(r"^>KEY1$", re.IGNORECASE): "This is key1 pattern",
    re.compile(r"^>?KEY2.*", re.IGNORECASE): "Key2 rooted pattern",
    re.compile(r"^>key.*>Leaf", re.IGNORECASE): "Key rooted leaf pattern",
    'key2': "This is key2",
    'Key2>leaf': "leaf under Key2",
    'key2>sub>leaf': "leaf of 3 levels",
    'leaf': 'leaf only'
}


def test_matched_keys():
    expectations = {">key1": 4, ">Key3>else>leaf": 2, "key2>": 1}

    for k, count in expectations.items():
        matched = matched_keys(k, test_dict.keys(), True, True)
        logger.info(matched)
        assert len(matched) == count


def test_get_matched_keys_by_default():
    candidates = [' id ', 'kid', 'id_account ', 'accountId ', 'name', 'address', ' _ID', ' _id_ ']
    keys = get_matched_keys(candidates, key_denoted_by_id)
    logger.info(keys)
    assert len(keys) == 5

    keys = get_matched_keys(candidates, key_denoted_by_id, False)
    logger.info(keys)
    assert len(keys) == 3


def test_get_matched_keys_with_knowns():
    candidates = ['id', 'kid', 'id_account ', 'accountId', 'name', 'address', ' _ID', ' _id_ ']
    keys = get_matched_keys(candidates, None, False, 'id', 'accountId', '_id')
    logger.info(keys)
    assert len(keys) == 2

    keys = get_matched_keys(candidates, None, True, 'ID', 'accountId', '_id')
    logger.info(keys)
    assert len(keys) == 3



def test_get_matched_keys_with_predicate():
    def ends(k, case_ignored):
        return k.endswith('id')

    candidates = [' id ', 'kid', 'id_account ', 'accountId ', 'name', 'address', ' _ID', ' _id_ ']
    keys = get_matched_keys(candidates, ends)
    logger.info(keys)
    assert len(keys) == 1

    def contains(k, case_ignored):
        return ('id' in k.casefold()) if case_ignored else ('id' in k)

    keys = get_matched_keys(candidates, contains, False)
    logger.info(keys)
    assert len(keys) == 4

    keys = get_matched_keys(candidates, contains, True)
    logger.info(keys)
    assert len(keys) == 6


