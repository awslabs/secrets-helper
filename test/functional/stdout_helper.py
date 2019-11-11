"""This is a simple script to help with cross-platform testing.

All it does is echo any CLI argument to stdout.
"""
import sys

print(*sys.argv[1:])  # noqa: T001
