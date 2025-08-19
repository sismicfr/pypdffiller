pypdffiller
===========

|Test| |PyPI| |Python| |Code Style| |Pre-Commit| |License|

``pypdffiller`` is a free and open source pure-Python 3 library for PDF form processing. It contains the essential
functionalities needed to interact with PDF forms:

- Inspect what data a PDF form needs to be filled with.
- Fill a PDF form by simply creating a Python dictionary.

Installation
------------

As of first version, ``pypdffiller`` is compatible with Python 3.9+.

Use ``pip`` to install the latest stable version of ``pypdffiller``:

.. code-block:: console

   $ pip install --upgrade python-pdffiller

The current development version is available on both `GitHub.com
<https://github.com/sismicfr/pypdffiller>`__ and can be
installed directly from the git repository:

.. code-block:: console

   $ pip install git+https://github.com/sismicfr/pypdffiller.git


Bug reports
-----------

Please report bugs and feature requests at
https://github.com/sismicfr/pypdffiller/issues.


Documentation
-------------

The full documentation for CLI and API is available at https://pypdffiller.readthedocs.org/en/stable/.

Build the docs
~~~~~~~~~~~~~~

We use ``tox`` to manage our environment and build the documentation:

.. code-block:: console

   $ pip install tox
   $ tox -e docs

Executable
----------

In addition to the **Python** package, a standalone executable can be built using **PyInstaller**.

Build the executable
~~~~~~~~~~~~~~~~~~~~

We use ``tox`` to manage our environment and build the executable:

.. code-block:: console

   $ pip install tox
   $ tox -e installer

.. code-block:: console

   $ make exe

Contributing
------------

For guidelines for contributing to ``pypdffiller``, refer to `CONTRIBUTING.rst <https://github.com/sismicfr/pypdffiller/blob/main/CONTRIBUTING.rst>`_.


.. |Test| image:: https://github.com/sismicfr/pypdffiller/workflows/Test/badge.svg
   :target: https://github.com/sismicfr/pypdffiller/actions
   :alt: Test

.. |PyPI| image:: https://img.shields.io/pypi/v/pypdffiller?label=PyPI&logo=pypi
   :target: https://badge.fury.io/py/pypdffiller
   :alt: PyPI

.. |Read the Docs| image:: https://img.shields.io/readthedocs/pypdffiller?label=Documentation&logo=Read%20the%20Docs
   :target: https://sismicfr.github.io/pypdffiller
   :alt: Docs

.. |Python| image:: https://img.shields.io/pypi/pyversions/pypdffiller.svg?label=Python&logo=Python
   :target: https://pypi.python.org/pypi/pypdffiller
   :alt: Python

.. |Code Style| image:: https://img.shields.io/badge/code%20style-black-000000.svg?label=Code%20Style
   :target: https://github.com/python/black
   :alt: Code Style

.. |Pre-Commit| image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&label=Pre-Commit
   :target: https://github.com/pre-commit/pre-commit
   :alt: Pre-Commit

.. |License| image:: https://img.shields.io/github/license/sismicfr/pypdffiller?label=License
   :target: https://github.com/sismicfr/pypdffiller/blob/main/COPYING
   :alt: License
