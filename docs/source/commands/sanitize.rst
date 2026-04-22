.. _commands_sanitize:

pdffiller sanitize
==================

.. code-block:: text

    $ pdffiller sanitize -h
    usage: pdffiller sanitize [-o OUTPUT_PATH] [--deep] [-L PATH] [-V [LEVEL]] [-f NAME] [-h] [INPUT_PATH]

    Sanitize a PDF by removing MaxLen constraints from text fields.
    This fixes PDFs where MaxLen is incorrectly set, causing text truncation.

    positional arguments:
      INPUT_PATH            Path to the input PDF file.

    options:
      -o OUTPUT_PATH, --output OUTPUT_PATH
                            Path to the output PDF file.
      --deep                Perform a deep sanitization: also clear the Comb flag
                            from text fields.
      -f NAME, --format NAME
                            Output format: text or json. Defaults to text.
      -L PATH, --log-file PATH
                            Send output to PATH instead of stderr.
      -V [LEVEL], --verbosity [LEVEL]
                            Level of detail of the output. Valid options from less verbose to more
                            verbose: -Vquiet, -Verror, -Vwarning, -Vnotice, -Vstatus, -V or -Vverbose, -VV or
                            -Vdebug, -VVV or -vtrace
      -h, --help            show this help message and exit

Sanitizes a single input PDF by removing ``/MaxLen`` constraints from text fields.
This fixes PDFs where ``/MaxLen`` is incorrectly set on widget annotations or
inherited from parent field dictionaries, causing text truncation when filling forms.

By default (light mode), fields with the Comb flag (``Bande de X caracteres`` in Adobe) are
**skipped**, as their ``/MaxLen`` is intentional. Only text fields without the Comb flag are sanitized.

With the ``--deep`` option, **all** text fields are sanitized: ``/MaxLen`` is removed and
the Comb flag (bit 25 of ``/Ff``) is also cleared.

.. code-block:: text

    pdffiller sanitize -o output.pdf input.pdf
    pdffiller sanitize --deep -o output.pdf input.pdf
    pdffiller sanitize -f json -o output.pdf input.pdf

The ``pdffiller sanitize`` command will:

* Load the input PDF file
* Walk through all text fields and their parent field dictionaries
* Skip fields with the Comb flag (unless ``--deep`` is used)
* Remove ``/MaxLen`` entries from each node in the hierarchy
* With ``--deep``: also clear the Comb flag (``Bande de X caracteres``) from ``/Ff``
* Save the sanitized PDF to the output path
* Report all sanitized fields (name, type, and previous MaxLen value)

Output formats
--------------

**Text** (default):

.. code-block:: text

    ----------
    FieldName: nom_souscripteur
    FieldType: Text
    MaxLen: 4
    ----------
    FieldName: prenom_souscripteur
    FieldType: Text
    MaxLen: 4

**JSON** (``-f json``):

.. code-block:: json

    [
        {
            "FieldName": "nom_souscripteur",
            "FieldType": "Text",
            "MaxLen": 4
        },
        {
            "FieldName": "prenom_souscripteur",
            "FieldType": "Text",
            "MaxLen": 4
        }
    ]
