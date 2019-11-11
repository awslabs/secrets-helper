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
"""Helper utilities for integration tests."""
import json
from dataclasses import dataclass
from pathlib import Path

import boto3
import pytest
from moto import mock_secretsmanager

from secrets_helper._commands import cli

COMMAND_NAME = "secrets-helper"

HERE = Path(__file__).parent
STDOUT_HELPER = HERE / "stdout_helper.py"
STDERR_HELPER = HERE / "stderr_helper.py"
ENV_HELPER = HERE / "env_helper.py"

FAKE_REGION = "us-west-2"
FAKE_SECRET_VALUES = {
    "secret-1": {"a": "ONE", "b": "TWO"},
    "secret-2": {"c": "THREE", "d": "FOUR"},
    "twine-secret": {"username": "0cool", "password": "hunter2"},
}


@pytest.fixture(autouse=True)
def fake_region(monkeypatch):
    monkeypatch.setenv("AWS_DEFAULT_REGION", FAKE_REGION)


@dataclass
class ConfigFile:
    placeholder: str
    body: str


SIMPLE_CONFIG_FILE = ConfigFile(
    placeholder="1174a9f5-fa22-48c0-be89-8b39f14864b0",
    body="""
[secrets-helper.env]
a=AYE
b=BEE
c:CEE
d:DEE
""",
)
COMPLEX_CONFIG_FILE = ConfigFile(
    placeholder="43a3df70-94bd-454d-9e80-106f259a5e3e",
    body=f"""
[secrets-helper.settings]
profile=twine
secrets=
    secret-1
    secret-2
    twine-secret

{SIMPLE_CONFIG_FILE.body}
""",
)
CONFIG_FILES = dict(simple=SIMPLE_CONFIG_FILE, complex=COMPLEX_CONFIG_FILE)


def run_test_command(args):
    exit_code = None
    try:
        cli.main(args=args, prog_name=COMMAND_NAME)
    except SystemExit as error:
        exit_code = error.args[0]

    assert exit_code is not None
    return exit_code


@pytest.fixture(autouse=True)
def fake_secrets():
    with mock_secretsmanager():
        sm = boto3.client("secretsmanager", region_name=FAKE_REGION)
        for name, value in FAKE_SECRET_VALUES.items():
            sm.create_secret(Name=name, SecretString=json.dumps(value))
        yield


@pytest.fixture
def config_files(tmpdir):
    files = {}
    for name, values in CONFIG_FILES.items():
        config = tmpdir.join(f"{name}.config")
        config.write(values.body)
        files[values.placeholder] = str(config)
    yield files


def patch_args(args, files):
    for placeholder, value in files.items():
        return args.replace(placeholder, value)
