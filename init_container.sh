#!/bin/bash
echo "Running init_container.sh, use this script to install libraries etc."


pre-commit install

pip install -e .
