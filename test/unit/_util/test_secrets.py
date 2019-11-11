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
"""Unit tests to ``secrets_helper._util.secrets``."""
import json
from typing import Iterator, List

import click
import pytest

import secrets_helper._util.secrets
from secrets_helper._util.secrets import _get_raw_secret_values, load_secrets, prep_secrets

from ...functional.functional_test_utils import fake_region  # noqa: F401 pylint: disable=unused-import
from ...functional.functional_test_utils import fake_secrets  # noqa: F401 pylint: disable=unused-import
from ...functional.functional_test_utils import FAKE_SECRET_VALUES

pytestmark = [pytest.mark.unit, pytest.mark.local]


def test_get_raw_secret_values_success():
    result = list(_get_raw_secret_values(secret_ids=FAKE_SECRET_VALUES.keys()))

    assert len(result) == len(FAKE_SECRET_VALUES)

    for (name, value) in result:
        expected = json.dumps(FAKE_SECRET_VALUES[name])
        assert value == expected


@pytest.mark.parametrize(
    "secret_ids",
    (
        pytest.param(["0cool"], id="unknown secret: raises ClientError"),
        pytest.param([b"invalid value"], id="invalid value: raises BotoCoreError"),
    ),
)
def test_get_raw_secret_values_fail(secret_ids):
    with pytest.raises(click.UsageError) as excinfo:
        list(_get_raw_secret_values(secret_ids=secret_ids))

    excinfo.match(r"Encountered AWS error for secret *")


def test_get_raw_secret_values_no_region(monkeypatch):
    monkeypatch.delenv("AWS_DEFAULT_REGION")
    with pytest.raises(click.UsageError) as excinfo:
        list(_get_raw_secret_values(secret_ids=["foo"]))

    excinfo.match("Unable to determine correct AWS region")


def _fake_get_raw_secret_values(return_value):
    def _fake(*, secret_ids: List[str]) -> Iterator[str]:
        for pos, each in enumerate(return_value):
            yield (f"mock-{pos}", each)

    return _fake


@pytest.mark.parametrize(
    "loaded_secrets, expected",
    (
        pytest.param([json.dumps({"a": "ONE"})], {"a": "ONE"}, id="one secret, one value"),
        pytest.param([json.dumps({"a": "ONE", "b": "TWO"})], {"a": "ONE", "b": "TWO"}, id="one secret, two values"),
        pytest.param(
            [json.dumps({"a": "ONE"}), json.dumps({"b": "TWO"})], {"a": "ONE", "b": "TWO"}, id="two secrets, two values"
        ),
    ),
)
def test_load_secrets_success(monkeypatch, loaded_secrets, expected):
    monkeypatch.setattr(
        secrets_helper._util.secrets, "_get_raw_secret_values", _fake_get_raw_secret_values(loaded_secrets)
    )

    actual = load_secrets(secret_ids=["secret ONE", "secret TWO"])

    assert actual == expected


@pytest.mark.parametrize(
    "loaded_secrets",
    (
        pytest.param([json.dumps({"a": "ONE"}), json.dumps({"a": "TWO"})], id="conflicting secret identifiers"),
        pytest.param(["not json"], id="non-json secret"),
    ),
)
def test_load_secrets_fail(monkeypatch, loaded_secrets):
    monkeypatch.setattr(
        secrets_helper._util.secrets, "_get_raw_secret_values", _fake_get_raw_secret_values(loaded_secrets)
    )

    with pytest.raises(click.UsageError):
        load_secrets(secret_ids=["secret ONE", "secret TWO"])


@pytest.mark.parametrize(
    "environment_mappings, secret_values, expected",
    (
        pytest.param({}, {}, {}, id="all empty"),
        pytest.param({"a": "b"}, {}, {}, id="no secrets"),
        pytest.param({"a": "b"}, {"a": "C"}, {"b": "C"}, id="one mapping"),
        pytest.param(
            {"a": "1", "b": "2", "c": "3", "d": "4"},
            {"a": "ONE", "b": "TWO", "d": "FOUR"},
            {"1": "ONE", "2": "TWO", "4": "FOUR"},
            id="uneven pairing",
        ),
    ),
)
def test_prep_secrets_succeed(environment_mappings, secret_values, expected):
    actual = prep_secrets(environment_mappings=environment_mappings, secret_values=secret_values)

    assert actual == expected


@pytest.mark.parametrize(
    "environment_mappings, secret_values", (pytest.param({}, {"a": "A"}, id="secret with no environment mapping"),)
)
def test_prep_secrets_fail(environment_mappings, secret_values):
    with pytest.raises(click.UsageError):
        prep_secrets(environment_mappings=environment_mappings, secret_values=secret_values)
