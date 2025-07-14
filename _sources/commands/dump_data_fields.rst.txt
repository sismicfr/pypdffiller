.. _commands_dump_data_fields:

pdffiller dump_data_fields
==========================

.. code-block:: text

    $ pdffiller dump_data_fields -h
    usage: pdffiller dump_data_fields [-L PATH] [-V [LEVEL]] [-f NAME] [-h] [INPUT_PATH]

    Dump form fields present in a pdf given its file path

    positional arguments:
      INPUT_PATH            Path to the input PDF file.

    options:
      -L PATH, --log-file PATH
                            Send output to PATH instead of stderr.
      -V [LEVEL], --verbosity [LEVEL]
                            Level of detail of the output. Valid options from less verbose to more 
                            verbose: -Vquiet, -Verror, -Vwarning, -Vnotice, -Vstatus, -V or -Vverbose, -VV or
                            -Vdebug, -VVV or -vtrace
      -h, --help            show this help message and exit

Reads a single input PDF file and reports form field statistics to stdout. Does not create a new PDF.

.. code-block:: text

    pdffiller dump_data_fields input.pdf

The ``pdffiller fill-form`` command will:

* Load and parse the input pdf file
* Dump all form fields to stdout
