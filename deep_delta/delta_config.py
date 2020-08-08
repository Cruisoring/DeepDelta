from __future__ import annotations
from enum import Flag


class DeltaConfig(Flag):
    """Config how to construct a DeepDelta instance with desirable behaviours.

    Flags are used to keep the settings in bitwise manner that can be combined with '|' operator.
    It is possible to define Enum of multiple options with proper mask bits: e.g. 3 bits for options of 5 to 8.
    """

    CaseIgnored = 0b11 << 0
    KeyCaseIgnored = 1 << 0
    ValueCaseIgnored = 1 << 1

    SpaceTrimmed = 0b11 << 2
    KeySpaceTrimmed = 1 << 2
    ValueSpaceTrimmed = 1 << 3

    IdAsKey = 1 << 4

    NoneUnequalDefault = 1 << 5

    MissingAsNone = 1 << 6

    # The output would keep the raw values if the flag is set
    OutputKeepAllDetails = 1 << 7
    # The output would use a boolean indicator of if delta exist: True if yes, False if left & right values are equal
    OutputWithDeltaIndicator = 1 << 8
    # The output would include types of the left and right values if the flag is set
    OutputIncludeValueTypes = 1 << 9

    # Mask of 2-bits flag below show how delta is represented
    OutputDeltaFormatMask = 0b11 << 10
    # the delta would be presented as tuples including left and right values in sequence
    OutputDeltaAsTuple = 0b00 << 10
    # the delta would be presented as dicts like: {'LEFT': left_value, 'RIGHT': right_value} by default
    OutputDeltaAsDict = 0b01 << 10
    # the delta would be presented as strings like: 'left_value | right_value' by default
    OutputDeltaAsStr = 0b10 << 10
    # any other output to be customised
    OutputDeltaAsCustom = 0b11 << 10

    # Mask of 5-bits including flags of OutputKeepAllDetails, OutputWithDeltaIndicator, OutputIncludeValueTypes
    # and the 2-bits OutputDeltaFormatMask
    OutputFormatMask = 0b11111 << 7

    # Default output format: None when no difference, tuple of (left_repr, right_repr) if left != right
    OutputDefault = 0x00000 << 7
    # Default output format with leading delta indicator: None when no difference,
    # tuple of (indicator, left_repr, right_repr) if left != right, like (True, 123, 'ok') and (False, 123, '123')
    OutputWithFlag = OutputDefault | OutputWithDeltaIndicator
    # Tuple with is_dif flag and value types
    OutputAllDetails = OutputKeepAllDetails | OutputWithFlag | OutputIncludeValueTypes
    # Dict of both left&right if is_dif, otherwise None
    OutputNoneOrDict = OutputDefault | OutputDeltaAsDict
    # Dict of both raw of left&right if is_dif, otherwise None
    OutputNoneOrDictRaw = OutputNoneOrDict | OutputKeepAllDetails
    # Str of both left&right if is_dif, otherwise None
    OutputNoneOrStr = OutputDefault | OutputDeltaAsStr
    # Str of both raw of left&right if is_dif, otherwise None
    OutputNoneOrStrRaw = OutputNoneOrStr | OutputKeepAllDetails

    def matches(self, flags: DeltaConfig, mask: DeltaConfig = None) -> bool:
        """Detect if this DeltaConfig instance has concerned flag.

        :param flags: the flags to be checked, can be used as mask if it is one bit flag.
        :param mask: the optional mask to keep only concerned flag bits.
        :return: True if the concerned flags are matched, otherwise False.
        """
        return self & (mask or flags) == flags

