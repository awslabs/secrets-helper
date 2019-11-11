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
import os

SECRET_ID_VAR = "SECRETS_HELPER_TEST_SECRETS"


def get_all_secret_ids():
    raw_values = os.environ.get(SECRET_ID_VAR, "")
    values = [v.strip() for v in raw_values.split(",")]

    if not values:
        raise EnvironmentError(
            f'The "{SECRET_ID_VAR}" variable MUST be set to a comma-delimited list of secret IDs'
            f" in order to run integration tests."
        )

    return values
