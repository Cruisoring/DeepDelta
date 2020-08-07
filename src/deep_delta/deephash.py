import abc
from typing import List, Set


class DeepHashInterface(metaclass=abc.ABCMeta):

    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'deep_indexes') and callable(subclass.deep_indexes)
                and hasattr(subclass, 'deep_hashcodes') and callable(subclass.deep_hashcodes)
                and hasattr(subclass, 'hashcode') and callable(subclass.hashcode)) \
               or NotImplemented

    @abc.abstractmethod
    def deep_indexes(self, obj: object) -> List[List[int]]:
        pass

    @abc.abstractmethod
    def deep_hashcodes(self, obj: object) -> Set[int]:
        pass

    @abc.abstractmethod
    def hashcode(self, obj: object) -> int:
        pass


class DeepHash(DeepHashInterface):

    def deep_indexes(self, obj: object) -> List[List[int]]:
        """ Python version of getDeepIndexes() of
        https://github.com/Cruisoring/functionExtensions/blob/master/src/main/java/io/github/cruisoring/TypeHelper.java
        Return an array of int[] to get the node type and indexes to access EVERY node elements of the concerned
        object.

        :param obj: any object hashable or not
        :return:
        """
        import collections.abc as abc
        issubclass(list, abc.Iterable)
        pass

    def deep_hashcodes(self, obj: object) -> Set[int]:
        pass

    def hashcode(self, obj: object) -> int:
        pass

