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
"""Utilities for processing config files."""
import configparser
import itertools
from dataclasses import dataclass
from typing import IO, Dict, List, Optional

import click

from ..identifiers import CONFIG_ENV_GROUP, CONFIG_SETTINGS_GROUP, KNOWN_CONFIGS

__all__ = ("load_config",)


@dataclass
class HelperConfig:
    """Command configuration metadata.

    :param list secret_ids: Secret IDs to retrieve
    :param dict environment_mappings: All environment mappings to use
    :param str profile: Name of environment mapping profile to use
    """

    secret_ids: List[str]
    environment_mappings: Dict[str, str]
    profile: Optional[str] = None


def _merge_key_ids(*, config_list: List[str], user_input_list: List[str]) -> List[str]:
    """Merge two lists of key IDs, retaining order, with no duplicates.

    :param list config_list: List of key IDs from config file
    :param list user_input_list: List of key IDs from user input
    :returns: Merged list containing all key IDs
    :rtype: list
    """
    values = user_input_list.copy()

    for val in config_list:
        if val not in values:
            values.append(val)

    return values


def _merge_mappings(*, config_mapping: Dict[str, str], profile_mapping: Dict[str, str]) -> Dict[str, str]:
    """Merge two mappings, raising errors if any keys or mappings conflict.

    :param dict config_mapping: Mappings from config file
    :param dict profile_mapping: Mappings from profile
    :returns: Merged mappings
    :rtype: dict
    :raises click.UsageError: if any keys are repeated
    :raises click.UsageError: if any keys map to the same value
    """
    mappings: Dict[str, str] = {}
    for key, value in itertools.chain(profile_mapping.items(), config_mapping.items()):
        if key in mappings:
            raise click.UsageError(f'Key "{key}" already in environment mapping.')

        if value in mappings.values():
            raise click.UsageError(f'Another key already maps to environment variable "{value}".')

        mappings[key] = value

    return mappings


def _mapping_from_profile_names(*, config_profile: Optional[str], user_profile: Optional[str]) -> Dict[str, str]:
    """Load environment mapping for profile identified in config OR user options.

    :param str config_profile: Profile name from config file
    :param str user_profile: Profile name from user options
    :return: Environment mapping for specified profile (or empty mapping if none specified)
    :raises click.UsageError: if profile name is set both in config file and in user options
    :raises click.UsageError: if profile name is not known
    """
    if config_profile is not None and user_profile is not None:
        raise click.UsageError(
            f'Profile "{config_profile}" set in config profile and profile "{user_profile}" set in user options.'
            "You must only specify profile once."
        )

    if config_profile is None and user_profile is None:
        return {}

    profile_name = user_profile if user_profile is not None else config_profile

    try:
        return KNOWN_CONFIGS[profile_name]
    except KeyError:
        raise click.UsageError(f'Unknown profile "{profile_name}"')


def _load_config_from_file(*, config_file: IO, profile: Optional[str]) -> HelperConfig:
    """Load a Secrets Manager Helper config from a file.

    :param IO config_file: Open config file object
    :returns: Loaded config, having expanded and merged profile mappings
        and merged any user input secrets with config secrets
    :rtype: HelperConfig
    :raises click.UsageError: if profile name is set both in config file and in user options
    :raises click.UsageError: if profile name is not known
    """
    parser = configparser.ConfigParser()
    parser.read_file(config_file)

    # Load secret IDs from config file
    try:
        secret_ids = [s.strip() for s in parser[CONFIG_SETTINGS_GROUP]["secrets"].split()]
    except KeyError:
        secret_ids = []

    # Load profile name from config file
    try:
        config_profile: Optional[str] = parser[CONFIG_SETTINGS_GROUP]["profile"]
    except KeyError:
        config_profile = None

    profile_map = _mapping_from_profile_names(config_profile=config_profile, user_profile=profile)

    # Load config mapping from config
    try:
        config_map = dict(parser[CONFIG_ENV_GROUP])
    except KeyError:
        config_map = {}

    # Merge config and profile mappings
    environment_mappings = _merge_mappings(config_mapping=config_map, profile_mapping=profile_map)

    return HelperConfig(secret_ids=secret_ids, environment_mappings=environment_mappings)


def load_config(*, config: Optional[IO], profile: Optional[str], secret_ids: List[str]) -> HelperConfig:
    """Load config from file and/or user-specified options.

    :param IO config: Open config file object
    :param str profile: Pre-defined mapping profile name
    :param list secret_ids: List of user-input secret IDs
    :returns: Loaded config, having expanded and merged profile mappings
        and merged any user input secrets with config secrets
    :rtype: HelperConfig
    """
    if config is not None:
        loaded_config = _load_config_from_file(config_file=config, profile=profile)
    else:
        loaded_config = HelperConfig(secret_ids=[], environment_mappings={})

    if profile is not None:
        profile_env_map = KNOWN_CONFIGS[profile]
    else:
        profile_env_map = {}

    all_secret_ids = _merge_key_ids(config_list=loaded_config.secret_ids, user_input_list=secret_ids)
    all_environment_mappings = _merge_mappings(
        config_mapping=loaded_config.environment_mappings, profile_mapping=profile_env_map
    )

    if not all_secret_ids:
        raise click.UsageError("No secret IDs provided")

    if not all_environment_mappings:
        raise click.UsageError("No environment mappings provided")

    return HelperConfig(secret_ids=all_secret_ids, environment_mappings=all_environment_mappings)
