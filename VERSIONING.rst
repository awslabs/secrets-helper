*****************
Versioning Policy
*****************

This project's versioning follows `semantic versioning`_ standards.

Major versions
==============

Major version changes are significant and expected to break backwards compatibility.

Minor versions
==============

Minor version changes will not break compatibility between the previous minor versions.
Minor version changes will also involve addition of optional features and non-breaking enhancements.
Additionally, any change to the version of a dependency is a minor version change.

Patch versions
==============

Patch versions changes are meant only for bug fixes,
and will not break compatibility of the current major version.
A patch release might contain a collection of minor bug fixes,
or individual major and security bug fixes, depending on severity.

Semantic Commits
****************

We seek to increase clarity at all levels of the update and releases process.
We require pull requests adhere to the `Conventional Commits`_ spec,
which can be summarized as follows:

* Commits that would result in a semver **major** bump must start with ``BREAKING CHANGE:``.
* Commits that would result in a semver **minor** bump must start with ``feat:``.
* Commits that would result in a semver **patch** bump must start with ``fix:``.

* We allow squashing of commits
  provided that the squashed message adheres the the above message format.

* It is acceptable for some commits in a pull request to not include a semantic prefix
  as long as a later commit in the same pull request contains a meaningful encompassing semantic message.


.. _semantic versioning: https://semver.org/
.. _Conventional Commits: https://conventionalcommits.org/
