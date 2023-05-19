====================================================
eulertools: Multilanguage competitive coding toolbox
====================================================

.. image:: https://github.com/spapanik/eulertools/actions/workflows/tests.yml/badge.svg
  :alt: Tests
  :target: https://github.com/spapanik/eulertools/actions/workflows/tests.yml
.. image:: https://img.shields.io/github/license/spapanik/eulertools
  :alt: License
  :target: https://github.com/spapanik/eulertools/blob/main/LICENSE.txt
.. image:: https://img.shields.io/pypi/v/eulertools
  :alt: PyPI
  :target: https://pypi.org/project/eulertools
.. image:: https://pepy.tech/badge/eulertools
  :alt: Downloads
  :target: https://pepy.tech/project/eulertools
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
  :alt: code style: black
  :target: https://github.com/psf/black
.. image:: https://img.shields.io/badge/build%20automation-yamk-success
  :alt: build automation: yam
  :target: https://github.com/spapanik/yamk
.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v1.json
  :alt: Lint: ruff
  :target: https://github.com/charliermarsh/ruff

``eulertools`` offers a tool to run/test/compare problems in for competitive programming,
or interview preparation, for example from `Project Euler`_, `leetcode`_, `topcoder`_ and others.


In a nutshell
-------------

Installation
^^^^^^^^^^^^

The easiest way is to use `pipx`_ to install ``eulertools``.

.. code:: console

   $ pipx install eulertools

This is the only officially supported way of installing it.
As ``eulertools`` require python 3.11+, please make sure that
this is the version used by your system, or use a tool like
`pyenv`_ to create a shell with such a python version.

Usage
^^^^^

``eulertools`` provides a cli command called ``euler``, which has the following subcommands:

::

    compare: Compare the timings between different languages
    generate: Generate a template for a new problem from the language template
    run: Run (and test) problems for various language implementations
    statement: Show the problem statement and the hint for the solution
    time: Run the timings for a specific problem

For the required project structure, please view the detailed `Documentation`_.

Links
-----

- `Documentation`_
- `Changelog`_


.. _Changelog: https://github.com/spapanik/eulertools/blob/main/CHANGELOG.rst
.. _Documentation: https://eulertools.readthedocs.io/en/latest/
.. _pipx: https://pypa.github.io/pipx/
.. _pyenv: https://github.com/pyenv/pyenv
.. _Project Euler: https://projecteuler.net/
.. _leetcode: https://leetcode.com/
.. _topcoder: https://www.topcoder.com/
