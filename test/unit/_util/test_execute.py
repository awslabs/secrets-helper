# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
"""Unit tests to ``secrets_helper._util.command``."""
import os
from typing import Iterable, List
from unittest.mock import Mock

import click
import pytest

import secrets_helper._util.execute
from secrets_helper._util.execute import (
    Tag,
    _clean_command_arguments,
    _inject_environment_variables,
    _tag_in_string,
    _value_to_triplet,
    run_command,
)

pytestmark = [pytest.mark.unit, pytest.mark.local]


@pytest.mark.parametrize(
    "args, expected",
    (
        ("ls", ["ls"]),
        ("ls -l", ["ls", "-l"]),
        ("ls -l thing/now", ["ls", "-l", "thing/now"]),
        ("ls -l thing/now/*", ["ls", "-l", "'thing/now/*'"]),
        ('find ./ -type f -name "*.py"', ["find", "./", "-type", "f", "-name", "'*.py'"]),
    ),
)
def test_clean_command_arguments(args: str, expected: List[str]):
    actual = _clean_command_arguments(args=args)

    assert actual == expected


_VALUES_CONTAINING_TAGS = (
    ("a{env:b}c", Tag.ENV, ("a", "b", "c")),
    ("{env:b}c", Tag.ENV, ("", "b", "c")),
    ("a{env:b}", Tag.ENV, ("a", "b", "")),
    ("{env:b}", Tag.ENV, ("", "b", "")),
    ("a{env:1}{env:2}a", Tag.ENV, ("a", "1", "{env:2}a")),
    ("0{env:1}{env:2}}a", Tag.ENV, ("0", "1", "{env:2}}a")),
)
_VALUES_NOT_CONTAINING_TAGS = (
    ("", Tag.ENV),
    ("awioeufhawoieufhjoawsiejvoawiejvoiwaoifa", Tag.ENV),
    ("}{env:", Tag.ENV),
    ("sijofe{env:", Tag.ENV),
)


@pytest.mark.parametrize("source, tag, expected", _VALUES_CONTAINING_TAGS)
def test_value_to_triplet(source: str, tag: Tag, expected: Iterable[str]):
    actual = _value_to_triplet(source=source, tag=tag)

    assert actual == expected


@pytest.mark.parametrize("source, tag", _VALUES_NOT_CONTAINING_TAGS)
def test_value_to_triplet_tag_not_in_source(source: str, tag: Tag):
    with pytest.raises(ValueError) as excinfo:
        _value_to_triplet(source=source, tag=tag)

    excinfo.match(f"Tag not in source: {tag}")


@pytest.mark.parametrize("source, tag", (i[:2] for i in _VALUES_CONTAINING_TAGS))
def test_tag_in_string_success(source: str, tag: Tag):
    assert _tag_in_string(source=source, tag=tag)


@pytest.mark.parametrize("source, tag", _VALUES_NOT_CONTAINING_TAGS)
def test_tag_in_string_fail(source: str, tag: Tag):
    assert not _tag_in_string(source=source, tag=tag)


_ENVIRONMENT_VARIABLES = {"A": "B", "C": "D", "LONG_NAME_WITH_LOTS_OF_SEPARATORS": "WAT", "BAK": "ANOTHER"}
_COMMAND_STRING_EXPANSIONS = (
    ("", ""),
    ("}{env:", "}{env:"),
    ("ASDF{env:C}", "ASDFD"),
    ("ASD{env:A}F", "ASDBF"),
    ("run the {env:LONG_NAME_WITH_LOTS_OF_SEPARATORS}", "run the WAT"),
    ("multiple {env:A} vals {env:C} here", "multiple B vals D here"),
)


@pytest.mark.parametrize("source, expected", _COMMAND_STRING_EXPANSIONS)
def test_inject_environment_variables_success(source: str, expected: str):
    actual = _inject_environment_variables(command_string=source, environment_variables=_ENVIRONMENT_VARIABLES)

    assert actual == expected


@pytest.mark.parametrize("source", (i[0] for i in _COMMAND_STRING_EXPANSIONS if i[0] != i[1]))
def test_inject_environment_variables_fail(source: str):
    with pytest.raises(click.UsageError) as excinfo:
        _inject_environment_variables(command_string=source, environment_variables={})

    excinfo.match(r"Unable to inject environment variable *")


@pytest.mark.parametrize(
    "raw_command, expected_command, extra_env_vars",
    (
        pytest.param("test command", ["test", "command"], {}, id="unmodified command, no additional variables"),
        pytest.param(
            "test command",
            ["test", "command"],
            {"a": "ONE", "b": "TWO"},
            id="unmodified command, some additional variables",
        ),
        pytest.param(
            "test command {env:z}",
            ["test", "command", "TWENTY_SIX"],
            {},
            id="modified command, no additional variables",
        ),
        pytest.param(
            "test command {env:a}-{env:b}",
            ["test", "command", "ONE-TWO"],
            {"a": "ONE", "b": "TWO"},
            id="modified command, some additional variables",
        ),
    ),
)
def test_run_command(monkeypatch, capsys, raw_command, expected_command, extra_env_vars):
    base_environ = {"z": "TWENTY_SIX", "y": "TWENTY_FIVE"}
    expected_env = dict(**base_environ, **extra_env_vars)
    mock_run = Mock()

    monkeypatch.setattr(os, "environ", base_environ.copy())
    monkeypatch.setattr(secrets_helper._util.execute.subprocess, "run", mock_run)

    test = run_command(raw_command=raw_command, extra_env_vars=extra_env_vars)

    assert test is mock_run.return_value
    mock_run.assert_called_once_with(expected_command, capture_output=True, env=expected_env, check=False, shell=False)

    captured_output = capsys.readouterr()

    assert not captured_output.out
    assert not captured_output.err


def test_run_command_env_override(monkeypatch, capsys):
    base_environ = {"z": "TWENTY_SIX", "y": "TWENTY_FIVE"}
    mock_run = Mock()

    monkeypatch.setattr(os, "environ", base_environ.copy())
    monkeypatch.setattr(secrets_helper._util.execute.subprocess, "run", mock_run)

    run_command(raw_command="test", extra_env_vars={"z": "OVERRIDE!"})

    mock_run.assert_called_once_with(
        ["test"], capture_output=True, env={"z": "OVERRIDE!", "y": "TWENTY_FIVE"}, check=False, shell=False
    )

    captured_output = capsys.readouterr()

    assert not captured_output.out

    assert 'Environment variable "z" will be overwritten in subprocess' in captured_output.err
