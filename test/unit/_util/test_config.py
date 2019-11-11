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
"""Unit tests to ``secrets_helper._util.config``."""
import io
from typing import IO, Optional

import click
import pytest

import secrets_helper._util.config
from secrets_helper._util.config import HelperConfig, _load_config_from_file, _mapping_from_profile_names, load_config
from secrets_helper.identifiers import KNOWN_CONFIGS

from ..unit_test_helpers import get_vector_filepath

pytestmark = [pytest.mark.unit, pytest.mark.local]


@pytest.mark.parametrize(
    "config_profile, user_profile, expected_profile",
    (
        pytest.param(None, None, None, id="no profile"),
        pytest.param("twine", None, "twine", id="profile in config only"),
        pytest.param(None, "twine", "twine", id="profile in user options only"),
    ),
)
def test_mapping_from_profile_names_success(config_profile, user_profile, expected_profile):
    test = _mapping_from_profile_names(config_profile=config_profile, user_profile=user_profile)

    expected = {} if expected_profile is None else KNOWN_CONFIGS[expected_profile]

    assert test == expected


@pytest.mark.parametrize(
    "config_profile, user_profile",
    (
        pytest.param("foo", None, id="nothing in user options, unknown in config"),
        pytest.param(None, "foo", id="unknown in user options, nothing in config"),
        pytest.param("twine", "twine", id="profile in both user options and config"),
    ),
)
def test_mapping_from_profile_names_fail(config_profile, user_profile):
    with pytest.raises(click.UsageError):
        _mapping_from_profile_names(config_profile=config_profile, user_profile=user_profile)


@pytest.mark.parametrize(
    "name, profile, expected",
    (
        ("simple", None, HelperConfig(secret_ids=[], environment_mappings=dict(a="VAL_A", b="VAL_B", c="VAL_C"))),
        (
            "simple",
            "twine",
            HelperConfig(
                secret_ids=[], environment_mappings=dict(a="VAL_A", b="VAL_B", c="VAL_C", **KNOWN_CONFIGS["twine"])
            ),
        ),
        (
            "simple-with-profile",
            None,
            HelperConfig(
                secret_ids=[], environment_mappings=dict(a="VAL_A", b="VAL_B", c="VAL_C", **KNOWN_CONFIGS["twine"])
            ),
        ),
        ("profile-only", None, HelperConfig(secret_ids=[], environment_mappings=KNOWN_CONFIGS["twine"])),
        (
            "complex",
            None,
            HelperConfig(
                secret_ids=["secret-1", "secret-2", "secret-3", "secret-4"],
                environment_mappings=dict(d="VAL_D", e="VAL_E", f="VAL_F", **KNOWN_CONFIGS["twine"]),
            ),
        ),
    ),
)
def test_load_config_from_file_success(name, profile, expected):
    with open(get_vector_filepath(name), "r") as f:
        actual = _load_config_from_file(config_file=f, profile=profile)

    assert actual == expected


@pytest.mark.parametrize(
    "name, profile",
    (
        pytest.param("simple", "foo", id="unknown profile"),
        pytest.param("simple-with-profile", "foo", id="profile set in both config and user options"),
    ),
)
def test_load_config_from_file_fail(name, profile):
    with open(get_vector_filepath(name), "r") as f:
        with pytest.raises(click.UsageError):
            _load_config_from_file(config_file=f, profile=profile)


def _load_config_scenarios_good():
    yield pytest.param(
        HelperConfig(secret_ids=["secret-1", "secret-2"], environment_mappings=dict(a="VAL_A")),
        None,
        ["secret-a", "secret-b"],
        HelperConfig(secret_ids=["secret-a", "secret-b", "secret-1", "secret-2"], environment_mappings=dict(a="VAL_A")),
        id="existing config, non-repeating secrets, no profile",
    )
    yield pytest.param(
        HelperConfig(secret_ids=["secret-1", "secret-2"], environment_mappings=dict(a="VAL_A")),
        None,
        ["secret-1", "secret-b"],
        HelperConfig(secret_ids=["secret-1", "secret-b", "secret-2"], environment_mappings=dict(a="VAL_A")),
        id="existing config, repeating secrets, no profile",
    )
    yield pytest.param(
        HelperConfig(secret_ids=["secret-1"], environment_mappings=dict(a="VAL_A")),
        "twine",
        [],
        HelperConfig(secret_ids=["secret-1"], environment_mappings=dict(a="VAL_A", **KNOWN_CONFIGS["twine"])),
        id="existing config, no user secrets, twine profile",
    )


def _fake_load_config_from_file(loaded_config):
    def _fake(*, config_file: IO, profile: Optional[str]) -> HelperConfig:
        return loaded_config

    return _fake


@pytest.mark.parametrize("loaded_config, profile, secret_ids, expected", _load_config_scenarios_good())
def test_load_config_success(monkeypatch, loaded_config, profile, secret_ids, expected):
    monkeypatch.setattr(
        secrets_helper._util.config, "_load_config_from_file", _fake_load_config_from_file(loaded_config)
    )

    actual = load_config(config=io.BytesIO(), profile=profile, secret_ids=secret_ids)

    assert actual == expected


def _load_config_scenarios_fail():
    yield pytest.param(
        HelperConfig(secret_ids=[], environment_mappings=dict()),
        None,
        ["secret-a", "secret-b"],
        id="no config, some secrets, no profile",
    )
    yield pytest.param(
        HelperConfig(secret_ids=[], environment_mappings=dict()),
        "twine",
        [],
        id="no config, no user secrets, twine profile",
    )
    yield pytest.param(
        HelperConfig(secret_ids=[], environment_mappings=dict(username="VAL_A")),
        "twine",
        [],
        id="config key conflicts with profile",
    )
    yield pytest.param(
        HelperConfig(secret_ids=[], environment_mappings=dict(asdf="TWINE_USERNAME")),
        "twine",
        [],
        id="config value conflicts with profile",
    )
    yield pytest.param(
        HelperConfig(secret_ids=[], environment_mappings=dict(asdf="TWINE_USERNAME")),
        None,
        [],
        id="mappings but no secrets",
    )
    yield pytest.param(
        HelperConfig(secret_ids=["secret-a"], environment_mappings={}), None, [], id="secrets but no mapping"
    )
    yield pytest.param(HelperConfig(secret_ids=[], environment_mappings={}), None, [], id="no configuration")


@pytest.mark.parametrize("loaded_config, profile, secret_ids", _load_config_scenarios_fail())
def test_load_config_fail(monkeypatch, loaded_config, profile, secret_ids):
    monkeypatch.setattr(
        secrets_helper._util.config, "_load_config_from_file", _fake_load_config_from_file(loaded_config)
    )

    with pytest.raises(click.UsageError):
        load_config(config=io.BytesIO(), profile=profile, secret_ids=secret_ids)


def test_load_config_no_config():
    with pytest.raises(click.UsageError):
        load_config(config=None, profile=None, secret_ids=[])
