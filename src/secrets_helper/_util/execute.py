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
"""Utilities for running a command."""
import os
import shlex
import subprocess  # nosec
from enum import Enum
from typing import Dict, Iterable, List

import click

__all__ = ("run_command",)


class Tag(Enum):
    """Command string injection marker tags."""

    def __init__(self, start: str, end: str):
        self.start = start
        self.end = end

    ENV = ("{env:", "}")


def _tag_in_string(*, source: str, tag: Tag) -> bool:
    """Determine if a specific tag is in a string.

    :param source: String to evaluate
    :param Tag tag: Tag to look for
    :returns: Decision
    """
    if tag.start not in source:
        return False

    if tag.end not in source[source.index(tag.start) + len(tag.start) :]:
        return False

    return True


def _value_to_triplet(source: str, tag: Tag) -> Iterable[str]:
    """Extract the first tag value from a string, splitting the source string into the parts before and after the tag.

    :param source: String to process
    :param Tag tag: Tag to split on
    :return: Split string values
    """
    if not _tag_in_string(source=source, tag=tag):
        raise ValueError(f"Tag not in source: {tag}")

    prefix, _value = source.split(tag.start, 1)

    value, suffix = _value.split(tag.end, 1)

    return prefix, value, suffix


def _inject_environment_variables(*, command_string: str, environment_variables: Dict[str, str]) -> str:
    """Inject environment variables into the command string.

    Environment variables must be identified using the ``{env:NAME}`` syntax.

    :param str command_string: Command string to modify
    :param dict environment_variables: Environment variables to use
    :return: Modified command string
    :rtype: str
    """
    final_command = ""
    remaining_command = command_string[:]

    while remaining_command:
        try:
            prefix, name, remaining_command = _value_to_triplet(source=remaining_command, tag=Tag.ENV)
        except ValueError:
            final_command += remaining_command
            remaining_command = ""
            continue

        final_command += prefix

        try:
            final_command += environment_variables[name]
        except KeyError:
            raise click.UsageError(
                f'Unable to inject environment variable "{name}" into command. Environment variable not found.'
            )

    return final_command


def _clean_command_arguments(*, args: str) -> List[str]:
    """Clean args from input for execution."""
    return [shlex.quote(i) for i in shlex.split(args)]


def run_command(*, raw_command: str, extra_env_vars: Dict[str, str]) -> subprocess.CompletedProcess:
    """Run a command with the provided environment variables.

    :param str raw_command: Raw command string to execute
    :param dict extra_env_vars: Environment variables to inject into subprocess environment
    :returns: resulting process data
    :rtype: subprocess.CompletedProcess
    """
    env = os.environ.copy()

    for key, value in extra_env_vars.items():
        if key in env:
            click.secho(f'Environment variable "{key}" will be overwritten in subprocess', fg="red", err=True)
        env[key] = value

    injected_command = _inject_environment_variables(command_string=raw_command, environment_variables=env)
    command_args = _clean_command_arguments(args=injected_command)

    # Using check=False because we process error cases in the upstream command that calls this function.
    # Using shell=False because we explicitly want to contain this subprocess execution.
    # Bandit is disabled for this line because they rightly will not allow any non-whitelisted calls to subprocess.
    return subprocess.run(command_args, capture_output=True, env=env, check=False, shell=False)  # nosec
