.. _commands_fill_form:

pdffiller fill_form
===================

.. code-block:: text

    $ pdffiller fill-form -h
    usage: pdffiller fill-form [-d DATA_PATH] [-o OUTPUT_PATH] [-f | --flatten | --no-flatten]
                               [-L PATH] [-V [LEVEL]] [-h] [INPUT_PATH]

    Fill an input PDF's form fields with the data from

    positional arguments:
      INPUT_PATH            Path to the input PDF file.

    options:
      -d DATA_PATH, --data DATA_PATH
                            Path to the data file defining the field/value pairs.
                            It can be a json or yaml file format.
                            It can be also - to read data file from stdin with JSON format.
      -i JSON_DATA, --input-data JSON_DATA
                            Input data with JSON format defining the field/value pairs.
      -o OUTPUT_PATH, --output OUTPUT_PATH
                            Path to the output PDF file.
      -f, --flatten, --no-flatten
                            Use this option to merge an input PDF's interactive form fields (and their data)
                            with the PDF's pages. Defaults to False.
      -L PATH, --log-file PATH
                            Send output to PATH instead of stderr.
      -V [LEVEL], --verbosity [LEVEL]
                            Level of detail of the output. Valid options from less verbose to more 
                            verbose: -Vquiet, -Verror, -Vwarning, -Vnotice, -Vstatus, -V or -Vverbose, -VV or
                            -Vdebug, -VVV or -vtrace
      -h, --help            show this help message and exit

Fills the single input PDF's form fields with the data from an input **json** or **yaml** file format.

When **-** is used to define input data file, **pdffiller** will read the data from *stdin* and assume that the input data are given as JSON format.

.. code-block:: text

    pdffiller fill-form -d input_data.json -o output.pdf --flatten input.pdf
    cat data.json | pdffiller fill-form -d - -o output.pdf --flatten input.pdf
    pdffiller fill-form -i '{"field_1": "text value", "radio_1": 1}' -o output.pdf --flatten input.pdf

The ``pdffiller fill-form`` command will:

* Load the input pdf file
* Load the input data file based on the file extension (ex: .json, .yaml, .yml)
* Update in memory all required pdf form fields based on values defined through the input data file
* Make all fields read-only if flatten option is enabled
* Dump the modified PDF file on the disk

Input data
----------

**pdffiller** supports only `json` and `yaml` file format for defining form field values.

.. code-block:: YAML

    "field_1": "text value"
    "radio_1": 1
    "checkbox_1": "On"
    "radio_2": 2

.. code-block:: JSON

    {
      "field_1": "text value",
      "radio_1": 1,
      "checkbox_1": "On",
      "radio_2": 2,
    }