.. _commands_embed_font:

pdffiller embed_font
====================

.. code-block:: text

    $ pdffiller embed_font -h
    usage: pdffiller embed-font [-o OUTPUT_PATH] [--font FONT_PATH] [--name NAME] [--size SIZE]
                                [--fields NAMES] [-L PATH] [-V [LEVEL]] [-f NAME] [-h]
                                [INPUT_PATH]

    Embed a TrueType font in a PDF form and make its text fields use it.
    fill_form then draws the values with that font.

    positional arguments:
      INPUT_PATH            Path to the input PDF file.

    options:
      -o OUTPUT_PATH, --output OUTPUT_PATH
                            Path to the output PDF file.
      --font FONT_PATH      Path to the TrueType font file (.ttf) to embed.
      --name NAME           Resource name of the font in the form. Default: the PostScript name of the
                            font.
      --size SIZE           Font size of the fields, 0 for the automatic size. Default: keep the size
                            of each field.
      --fields NAMES        Comma-separated names of the text fields to change. Default: all the text
                            fields.
      -L PATH, --log-file PATH
                            Send output to PATH instead of stderr.
      -V [LEVEL], --verbosity [LEVEL]
                            Level of detail of the output. Valid options from less verbose to more
                            verbose: -Vquiet, -Verror, -Vwarning, -Vnotice, -Vstatus, -V or -Vverbose,
                            -VV or -Vdebug, -VVV or -vtrace
      -f NAME, --format NAME
                            Select the output format: json
      -h, --help            show this help message and exit

Embeds a TrueType font file in the form resources of a PDF (``/AcroForm /DR``) and
sets the default appearance (``/DA``) of the text fields to that font. The other
fields, checkboxes and radio buttons, do not change.

.. code-block:: text

    pdffiller embed_font --font Marianne-Regular.ttf --fields Lastname,Firstname -o form.pdf input.pdf

After this command:

* :ref:`commands_fill_form` draws the values of these fields with the font, in a
  flattened PDF and in a PDF that stays fillable.
* A PDF viewer uses the font when a person types in the field.
* A field that already holds a value shows it with the font.

Each field keeps its font size and its colour, unless ``--size`` gives a size.
A size of 0 is the automatic size.

Limits:

* The font is embedded as a simple TrueType font in WinAnsi encoding (cp1252).
  This covers French and the other Western European languages, with the euro sign.
  For a character out of WinAnsi, :ref:`commands_fill_form` draws the value with the
  default font and writes a warning. The field still names the embedded font.
* The full font file is embedded, not a subset, because the values are not known
  yet. The PDF becomes larger by the size of the font file. :ref:`commands_fill_form`
  keeps the full font too.
* OpenType fonts with PostScript outlines (``.otf`` with CFF) are refused.
