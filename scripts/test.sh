#!/usr/bin/env bash
set -e

myPath=$(realpath "$0")
myDir1=$(dirname "$myPath")
rootDir=$(dirname "$myDir1")

echo "$rootDir/tests"
cd "$rootDir/tests"
python -m unittest *_test.py


echo
echo "$rootDir/pyglossary/plugin_lib"
cd "$rootDir/pyglossary/plugin_lib"
python -m unittest *_test.py
