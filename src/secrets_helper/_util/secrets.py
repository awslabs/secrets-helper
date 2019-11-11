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
"""Utilities for handling secrets."""
import json
from typing import Dict, Iterable, Iterator, Tuple

import boto3
import botocore.exceptions
import click

__all__ = ("load_secrets", "prep_secrets")


def _get_raw_secret_values(*, secret_ids: Iterable[str]) -> Iterator[Tuple[str, str]]:
    """Retrieve secret values from Secrets Manager.

    :param list secret_ids: All secret IDs to retrieve
    :returns: Raw secret values
    :rtype: iterable
    """
    try:
        secrets_manager = boto3.client("secretsmanager")
    except botocore.exceptions.NoRegionError:
        raise click.UsageError("Unable to determine correct AWS region")

    for name in secret_ids:
        try:
            response = secrets_manager.get_secret_value(SecretId=name)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as error:
            raise click.UsageError(f'Encountered AWS error for secret "{name}": "{error}"')

        yield (name, response["SecretString"])


def load_secrets(*, secret_ids: Iterable[str]) -> Dict[str, str]:
    """Load JSON-encoded secrets values.

    :param list secret_ids: All secret IDs to retrieve
    :returns: Mapping of secret identifiers to secret values
    :rtype: dict
    """
    values: Dict[str, str] = {}

    for secret_name, raw_secret in _get_raw_secret_values(secret_ids=secret_ids):
        try:
            secret_map = json.loads(raw_secret)
        except json.decoder.JSONDecodeError:
            raise click.UsageError(f'Secret "{secret_name}" value is not JSON formatted.')

        for key, value in secret_map.items():

            if key in values:
                raise click.UsageError(f'Key "{key}" already loaded!')

            values[key] = value

    return values


def prep_secrets(*, environment_mappings: Dict[str, str], secret_values: Dict[str, str]) -> Dict[str, str]:
    """Convert secrets from standardized name map to required environment variable map.

    :param dict environment_mappings: Mapping from secret identifiers to environment variable names
    :param dict secret_values: Mapping from secret identifiers to secret values
    :returns: Mapping from environment variable names to secret values
    :raises click.UsageError: if secrets contains an identifier that is not in environment_mappings
    """
    try:
        return {environment_mappings[key]: value for key, value in secret_values.items()}
    except KeyError as error:
        missing_key = error.args[0]
        raise click.UsageError(f'Identifier key "{missing_key}" not found in environment variable mapping.')
