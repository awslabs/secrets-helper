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
"""CLI commands."""
import functools
import sys
from typing import IO, Dict, Optional, Tuple

import click

from ._util.config import load_config
from ._util.execute import run_command
from ._util.secrets import load_secrets, prep_secrets
from .identifiers import KNOWN_CONFIGS, __version__

__all__ = ("cli",)


def _collect_secrets(func):
    @click.option("--secret", "secret_ids", multiple=True, required=False, help="Secrets Manager ARN")
    @click.option("--config", required=False, type=click.File("r"), help="Config file")
    @click.option(
        "--profile", required=False, type=click.Choice(list(KNOWN_CONFIGS.keys())), help="Command profile to use"
    )
    @functools.wraps(func)
    def wrapper(*, secret_ids: Tuple[str], config: Optional[IO], profile: Optional[str], **kwargs):
        if config is None and profile is None:
            raise click.UsageError("Either --config or --profile must be provided")

        helper_config = load_config(config=config, profile=profile, secret_ids=list(secret_ids))

        secret_values = load_secrets(secret_ids=helper_config.secret_ids)
        secret_env_vars = prep_secrets(
            environment_mappings=helper_config.environment_mappings, secret_values=secret_values
        )

        return func(secret_env_vars=secret_env_vars, **kwargs)

    return wrapper


@click.group()
@click.version_option(version=__version__)
def cli():
    """Enter CLI."""


@cli.command(context_settings=dict(allow_interspersed_args=False, ignore_unknown_options=True))
@_collect_secrets
@click.option("--command", required=True, help="Command to run")
def run(secret_env_vars: Dict[str, str], command: str):
    """Run a command with injected environment variables.

    :param dict secret_env_vars: Environment variables containing loaded secret values
    :param str command: Command to execute
    """
    result = run_command(raw_command=command, extra_env_vars=secret_env_vars)

    if result.stdout:
        click.echo(result.stdout)

    if result.stderr:
        click.echo(result.stderr, err=True)

    sys.exit(result.returncode)


@cli.command(context_settings=dict(allow_interspersed_args=False, ignore_unknown_options=True))
@_collect_secrets
def env(secret_env_vars: Dict[str, str]):
    """Print out secret environment variables for processing by ``env`` or a similar program.

    :param dict secret_env_vars: Environment variables containing loaded secret values
    """
    for key, value in secret_env_vars.items():
        click.echo(f'{key}="{value}"')
    sys.exit(0)
