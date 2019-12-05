MTGDeckConverter
================

Convert digital Magic The Gathering (R) deck lists between formats.
Please note that the conversion is lossy and may require online access, as not all formats provide all necessary
information to perform the conversion locally. This program relies on the scryfall.com API to perform information lookup,
if needed.

For example, an XMage deck list requires the collector numbers of all cards in the deck,
which a TappedOut CSV export does not provide. Thus to provide a conversion, the required numbers have to be looked up
online. On the other hand, XMage deck lists do not support TappedOut custom card categories, card language,
grading, foil state, and certain deck configurations, like Commander/Oathbreaker decks with sideboards.
These features will be *lost* during the conversion.

In the other direction, XMage saves a fully manual deck layout with rows and columns of card stacks in the editor,
which TappedOut does not support. Thus the manual card arrangement will be lost when converting from XMage to TappedOut.

Supported formats
-----------------

This section lists the currently supported deck formats.

Input formats
+++++++++++++

These formats can be read:

- Currently None

Output formats
++++++++++++++

These formats can be written:

- Currently None


Requirements
------------

- Python 3.7 or newer (3.6 may work, but is untested)

Install
-------

Install from PyPI using :code:`pip3 install MTGDeckConverter`
(NOTE: CURRENTLY NOT IMPLEMENTED. This will work at some point in the future, when this note disappears.)

Alternatively, to install the latest version from a local repository checkout,
open a terminal at the root level of your checkout (contains ``setup.py`` and this README) and run:
:code:`pip3 install .` (Note the dot indicating the current directory).

As a third alternative, you can run the program directly from the repository checkout without installation.
The repository contains a simple runner script (named ``MTGDeckConverter-runner.py``) that can be used for this purpose.

Currently, there is no setup.exe or directly executable Python bundle for Windows platforms.

Usage
-----

Execute *MTGDeckConverter*.

Contributing
------------

If you want to contribute, pull requests that fix issues or add additional input or output formats are welcome.
Just open a PR on GitHub to discuss the additions.

Running the tests
+++++++++++++++++

Running the unit test suite is integrated into setup.py.
So to run the tests, execute :code:`python3 setup.py test` from the git checkout root directory.


The tests require:

- pytest
- PyHamcrest
- pyfakefs

About
-----

Copyright (C) 2019, Thomas Hess

This program is licensed under the GNU GENERAL PUBLIC LICENSE Version 3.
See the LICENSE file for details.
