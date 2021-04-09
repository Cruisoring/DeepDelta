from __future__ import annotations

from typing import Tuple, Any, Optional, Dict, Callable

from deepdelta.delta_config import DeltaConfig

TYPE_ABBREVIATIONS = {
    list: '[...]',
    set: '{,,}',
    dict: '{...}',
    tuple: '(...)'
}


class DeltaOutput:

    LEFT_KEY = 'LEFT'
    RIGHT_KEY = 'RIGHT'
    STR_FORMAT = '{0} | {1}'

    @staticmethod
    def get_value_abbrev(value: Any) -> Optional:
        if value is None:
            return None
        elif type(value) in TYPE_ABBREVIATIONS:
            return TYPE_ABBREVIATIONS[type(value)]
        else:
            return value

    @staticmethod
    def no_flag_tuple_abbrev(is_dif: bool, left: Any, right: Any) -> Tuple:
        return (DeltaOutput.get_value_abbrev(left), DeltaOutput.get_value_abbrev(right)) if is_dif else None

    @staticmethod
    def as_tuple(is_dif: bool, left: Any, right: Any) -> Tuple:
        return is_dif, left, right

    @staticmethod
    def as_none_or_tuple(is_dif: bool, left: Any, right: Any) -> Tuple:
        return (left, right) if is_dif else None

    @staticmethod
    def type_included(is_dif: bool, left: Any, right: Any) -> Tuple:
        return is_dif, left, right, type(left), type(right)

    @staticmethod
    def as_none_or_str_raw(is_dif: bool, left: Any, right: Any) -> Optional[str]:
        return DeltaOutput.STR_FORMAT.format(left, right) if is_dif else None

    @staticmethod
    def as_none_or_str(is_dif: bool, left: Any, right: Any) -> Optional[str]:
        return DeltaOutput.STR_FORMAT.format(DeltaOutput.get_value_abbrev(left), DeltaOutput.get_value_abbrev(right)) \
            if is_dif else None

    @staticmethod
    def as_none_or_dict_raw(is_dif: bool, left: Any, right: Any) -> Optional[Dict[str, Any]]:
        if not is_dif:
            return None
        else:
            return {DeltaOutput.LEFT_KEY: left,
                    DeltaOutput.RIGHT_KEY: right}

    @staticmethod
    def as_none_or_dict(is_dif: bool, left: Any, right: Any) -> Optional[Dict[str, Any]]:
        if not is_dif:
            return None
        else:
            return {DeltaOutput.LEFT_KEY: DeltaOutput.get_value_abbrev(left),
                    DeltaOutput.RIGHT_KEY: DeltaOutput.get_value_abbrev(right)}


Output_Buffer: Dict[DeltaConfig, Callable[[bool, Any, Any], Any]] = {
    DeltaConfig.OutputDefault: DeltaOutput.no_flag_tuple_abbrev,

    DeltaConfig.OutputWithFlag: DeltaOutput.as_tuple,
    DeltaConfig.OutputAllDetails: DeltaOutput.type_included,
    DeltaConfig.OutputNoneOrDict: DeltaOutput.as_none_or_dict,
    DeltaConfig.OutputNoneOrDictRaw: DeltaOutput.as_none_or_dict_raw,
    DeltaConfig.OutputDeltaAsStr: DeltaOutput.as_none_or_str,
    DeltaConfig.OutputNoneOrStrRaw: DeltaOutput.as_none_or_str_raw,
}


def set_output(config: DeltaConfig, output: Callable) -> Optional[Callable]:
    output_config = config & DeltaConfig.OutputFormatMask
    old_output = Output_Buffer[output_config] if output_config in Output_Buffer else None
    Output_Buffer[output_config] = output
    return old_output


def get_output(config: DeltaConfig) -> Callable[[bool, Any, Any], Any]:
    output_config = config & DeltaConfig.OutputFormatMask
    if output_config not in Output_Buffer:
        raise TypeError(f"Please specify output method to associate with {config}")

    output = Output_Buffer[output_config]
    if config.matches(DeltaConfig.OutputKeepAllDetails):
        return output
    else:
        return lambda is_dif, left, right: \
            output(is_dif, DeltaOutput.get_value_abbrev(left), DeltaOutput.get_value_abbrev(right))
