__version__ = '1.0.0'

import logging
import sys, os

package_path = os.path.realpath(os.path.dirname(__file__))
sys.path.append(package_path)
# print(sys.path)

from core import DeepDelta, DEFAULT_DELTA_CONFIG
from delta_config import DeltaConfig
from comparator import DEFAULT_TYPE_COMPARATOR, Comparator
from delta_output import TYPE_ABBREVIATIONS, DeltaOutput, Output_Buffer

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)8s %(message)s')

