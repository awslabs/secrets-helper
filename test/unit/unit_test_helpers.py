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
"""Helper utilities for unit tests."""
from pathlib import Path

__all__ = ("get_vector_filepath",)
HERE = Path(__file__).parent
VECTORS_DIR = HERE / ".." / "vectors"


def get_vector_filepath(name: str) -> str:
    return str(VECTORS_DIR / f"{name}.config")
