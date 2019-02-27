@echo off
pip install isort --quiet
isort tests pyheos --recursive
pip install -r test-requirements.txt --quiet
pylint tests pyheos
flake8 tests pyheos
pydocstyle tests pyheos