""" Sample command to compare two JSON files in the data folder:
python -m deep_delta data\widget1.json data\widget2.json
"""

import sys
import pathlib
import json
from typing import Any

from .core import DeepDelta


def load_obj(file_or_obj: str) -> Any:
    """Load the file or object as a JSON object."""
    file = pathlib.Path(file_or_obj.strip("'\""))
    if file.exists():
        with open(file, 'rt') as fp:
            data = json.load(fp)
            return data
    else:
        data = json.loads(file)
        return data


def main():
    segments = sys.argv[1:]
    if len(segments) != 2:
        print(f'Please specify two objects or files to compare.')
    data1, data2 = load_obj(segments[0]), load_obj(segments[1])
    delta = DeepDelta.compare(data1, data2)
    print(delta)


if __name__ == "__main__":
    main()

