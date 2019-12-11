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
"""Unique identifiers used by secrets-helper."""
__all__ = ("__version__", "CONFIG_SETTINGS_GROUP", "CONFIG_ENV_GROUP", "KNOWN_CONFIGS")
__version__ = "0.1.0"

CONFIG_NAME = "secrets-helper"
CONFIG_SETTINGS_GROUP = f"{CONFIG_NAME}.settings"
CONFIG_ENV_GROUP = f"{CONFIG_NAME}.env"
KNOWN_CONFIGS = dict(
    twine=dict(username="TWINE_USERNAME", password="TWINE_PASSWORD", url="TWINE_REPOSITORY_URL")  # nosec
)
