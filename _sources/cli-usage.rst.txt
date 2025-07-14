############################
Getting started with the CLI
############################

``pypdffiller`` provides a :command:`pdffiller` command-line tool to interact
with pdf files.

CLI
===

Output
------

The CLI also sends all the information, warning, and error messages to stderr, while keeping the final result in stdout, allowing multiple output formats
like --format=json or --format=text and using redirects to create files `--format=json` > myfile.json. 

The information provided by the CLI will be more structured and thorough so that it can be used more easily for automation, especially in Web-Server
or CI/CD systems.


Actions
-------

The ``pdffiller`` command expects at least one mandatory argument. This
argument is the action that you want to perform. For example:

.. code-block:: console

   $ pdffiller dump_data_fields test.pdf
   $ pdffiller fill_form input.pdf -d data.json -o output.pdf

Use the ``--help`` option to list the available action names:

.. code-block:: console

   $ pdffiller --help

Some actions require additional parameters. Use the ``--help`` option to
list mandatory and optional arguments for an action:

.. code-block:: console

   $ pdffiller dump_data_fields --help
   $ pdffiller fill_form --help
