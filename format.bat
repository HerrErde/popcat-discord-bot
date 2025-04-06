@echo off
autoflake --in-place --remove-all-unused-imports --remove-unused-variables --exclude=__init__.py -r .
isort . --ws
black .
pause