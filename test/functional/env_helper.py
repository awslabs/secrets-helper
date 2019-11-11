"""This is a simple script to help with cross-platform testing.

It emulates the *nix `env` command by printing out
any environment variables to stdout.
"""
import os

for key, value in os.environ.items():
    print(f"{key}={value}")  # noqa: T001
