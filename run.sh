#!/bin/bash
PASSWORD="ABCD1234"
python3 run.py --in-dir=./input/old_format/ --out-dir=./output/ --password=$PASSWORD --format=old
python3 run.py --in-dir=./input/new_format/ --out-dir=./output/ --password=$PASSWORD --format=new