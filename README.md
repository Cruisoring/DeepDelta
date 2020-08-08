# DeepDelta

## Overview

DeepDelta is a compact Python library to compare any two objects with a rich set of configurable options and comparators with any desirable output format.


## Installation

Install from PyPi:

`>pip install deep_delta`

Once installed, run following command to compare two JSON files:

`>python -m deep_delta 'c:\py\deep_delta\data\widget1.json' data\widget2.json`

With the sample files in the data folder, the output might be:

`{'widget': {'window': {'width': (500, 600)}, 'debug': ('on', 'off'), 'text': {'style': ('bold', 'ITALIC'), 'hoffset': (250, '200')}, 'image': {'alignment': ('center', 'left')}}}`


## How to use

The main function to be called is ![DeepDelta.compare()|]()


