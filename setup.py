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
"""secrets-helper."""
import io
import os
import re

from setuptools import find_packages, setup

VERSION_RE = re.compile(r"""__version__ = ['"]([0-9.]+)['"]""")
HERE = os.path.abspath(os.path.dirname(__file__))


def read(*args):
    """Read complete file contents."""
    return io.open(os.path.join(HERE, *args), encoding="utf-8").read()


def get_version():
    """Read the version from this module."""
    init = read("src", "secrets_helper", "identifiers.py")
    return VERSION_RE.search(init).group(1)


def get_requirements():
    """Read the requirements file."""
    raw_requirements = read("requirements.txt")
    requirements = []
    dependencies = []

    for req in raw_requirements.splitlines():
        req = req.strip()
        if not req:
            continue

        if req.startswith("#"):
            continue

        if "+" in req:
            dependencies.append(req)
        else:
            requirements.append(req)

    return requirements, dependencies


INSTALL_REQUIRES, DEPENDENCY_LINKS = get_requirements()


setup(
    name="secrets-helper",
    version=get_version(),
    packages=find_packages("src"),
    package_dir={"": "src"},
    url="https://github.com/awslabs/secrets-helper",
    author="Amazon Web Services",
    author_email="aws-cryptools@amazon.com",
    maintainer="Amazon Web Services",
    description="secrets-helper",
    long_description=read("README.rst"),
    long_description_content_type="text/x-rst",
    keywords="secrets-helper secrets_helper aws",
    data_files=["README.rst", "CHANGELOG.rst", "LICENSE", "requirements.txt"],
    license="Apache 2.0",
    python_requires=">=3.7",
    install_requires=INSTALL_REQUIRES,
    dependency_links=DEPENDENCY_LINKS,
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Security",
        "Topic :: Security :: Cryptography",
    ],
    entry_points=dict(console_scripts=["secrets-helper=secrets_helper._commands:cli"]),
)
