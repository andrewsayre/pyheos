@echo off
isort tests pyheos --recursive
black tests pyheos
pylint tests pyheos
flake8 tests pyheos --doctests