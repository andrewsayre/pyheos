@echo off
isort tests pyheos
black tests pyheos
pylint tests pyheos
flake8 tests pyheos --doctests