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
"""Functional tests to ``secrets_helper`` CLI."""
import shlex

import pytest

from secrets_helper import __version__

from .functional_test_utils import config_files  # noqa: F401 pylint: disable=unused-import
from .functional_test_utils import fake_region  # noqa: F401 pylint: disable=unused-import
from .functional_test_utils import fake_secrets  # noqa: F401 pylint: disable=unused-import
from .functional_test_utils import (
    COMMAND_NAME,
    ENV_HELPER,
    SIMPLE_CONFIG_FILE,
    STDERR_HELPER,
    STDOUT_HELPER,
    patch_args,
    run_test_command,
)

pytestmark = [pytest.mark.functional, pytest.mark.local]


def test_version(capsys):
    exit_code = run_test_command(["--version"])

    assert exit_code == 0

    captured_output = capsys.readouterr()
    assert captured_output.out == f"{COMMAND_NAME}, version {__version__}\n"


@pytest.mark.parametrize(
    "args, expected_stdout, expected_stderr",
    (
        pytest.param(
            "env --secret twine-secret --profile twine",
            'TWINE_USERNAME="0cool"\nTWINE_PASSWORD="hunter2"\n',
            "",
            id="single secret, user-selected mapping profile",
        ),
        pytest.param(
            f"env --secret secret-1 --config {SIMPLE_CONFIG_FILE.placeholder}",
            'AYE="ONE"\nBEE="TWO"\n',
            "",
            id="single secret, config mapping",
        ),
        pytest.param(
            f"env --secret secret-1 --secret secret-2 --config {SIMPLE_CONFIG_FILE.placeholder}",
            'AYE="ONE"\nBEE="TWO"\nCEE="THREE"\nDEE="FOUR"\n',
            "",
            id="multiple secrets, config mapping",
        ),
    ),
)
def test_env_command_success(capsys, config_files, args, expected_stdout, expected_stderr):
    args = patch_args(args, config_files)
    exit_code = run_test_command(shlex.split(args))

    captured_output = capsys.readouterr()

    assert exit_code == 0
    assert captured_output.out == expected_stdout
    assert captured_output.err == expected_stderr


@pytest.mark.parametrize(
    "args, expected_stdout, expected_stderr",
    (
        pytest.param(
            f"run --command 'python {ENV_HELPER}' --secret twine-secret --profile twine",
            "TWINE_USERNAME=0cool\nTWINE_PASSWORD=hunter2\n",
            "",
            id="passing env-vars to env",
        ),
        pytest.param(
            (
                f"run --command 'python {STDOUT_HELPER} WAT {{env:AYE}} WOW' "
                f"--secret secret-1 --config {SIMPLE_CONFIG_FILE.placeholder}"
            ),
            "WAT ONE WOW",
            "",
            id="interpolation with echo to stdout",
        ),
        pytest.param(
            (
                f"run --command 'python {STDERR_HELPER} WAT {{env:AYE}} WOW' "
                f"--secret secret-1 --config {SIMPLE_CONFIG_FILE.placeholder}"
            ),
            "",
            "WAT ONE WOW",
            id="interpolation with echo to stderr",
        ),
    ),
)
def test_run_command_success(capsys, config_files, args, expected_stdout, expected_stderr):
    args = patch_args(args, config_files)
    exit_code = run_test_command(shlex.split(args))

    captured_output = capsys.readouterr()

    assert exit_code == 0
    assert expected_stdout in captured_output.out
    assert expected_stderr in captured_output.err


@pytest.mark.parametrize(
    "args, expected_stdout, expected_stderr",
    (
        pytest.param(
            "env", "", "Either --config or --profile must be provided", id="neither config nor profile provided"
        ),
        pytest.param(
            "run --command foo",
            "",
            "Either --config or --profile must be provided",
            id="neither config nor profile provided",
        ),
    ),
)
def test_env_command_fail(capsys, config_files, args, expected_stdout, expected_stderr):
    args = patch_args(args, config_files)
    exit_code = run_test_command(shlex.split(args))

    captured_output = capsys.readouterr()

    assert exit_code != 0
    assert expected_stdout in captured_output.out
    assert expected_stderr in captured_output.err
