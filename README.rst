MTGDeckConverter
================

Convert digital Magic The Gathering (R) deck lists between formats.
Please note that the conversion is lossy and may require online access, as not all formats provide all necessary
information to perform the conversion locally. This program relies on the scryfall.com API data
to perform information lookup, if needed.

Limitations
-----------

There are certain limitations,
when one deck file format supports features that the other source or target format does not support.

For example, an XMage deck list requires the collector numbers of all cards in the deck,
which a TappedOut CSV export does not provide. Thus, to provide a conversion, the required numbers have to be looked up
using an additional card database as the data source.
On the other hand, XMage deck lists do not support TappedOut custom card categories, card language,
grading/card quality, foil state, and certain deck configurations, like Commander/Oathbreaker decks with sideboards.
These features will be *lost* during the conversion.

In the other direction, XMage saves a fully manual deck layout with rows and columns of card stacks in the editor,
which TappedOut does not support. Thus the manual card arrangement will be lost when converting from XMage to TappedOut.

Supported formats
-----------------

This section lists the currently supported deck formats.
Beware: Currently, as long as the Scryfall integration is missing, deck conversions are incomplete.

Input formats
+++++++++++++

These deck formats can be read:

- CSV files exported from https://tappedout.net

Output formats
++++++++++++++

These deck formats can be written:

- `XMage <http://xmage.de/>`_ deck lists


Requirements
------------

- Python 3.7 or newer (This program uses features added in 3.7, so earlier versions are definitely unsupported.)
- ``requests`` (`https://pypi.org/project/requests/ <https://pypi.org/project/requests/>`_)

Install
-------

At some point in the future, you’ll be able to install from PyPI using :code:`pip3 install MTGDeckConverter`
(NOTE: This program is currently NOT published on PyPI.
This will work at some point in the future, when this note disappears.)

Alternatively, to install the latest version from a local repository checkout,
open a terminal at the root level of your checkout (contains ``setup.py`` and this README) and run:
:code:`pip3 install .` (Note the dot indicating the current directory).

As a third alternative, you can run the program directly from the repository checkout without installation.
The repository contains a simple runner script (named ``MTGDeckConverter-runner.py``) that can be used for this purpose.

Currently, there is no setup.exe or directly executable Python bundle for Windows platforms.

Usage
-----

Currently, there is no main application.
You can explore what is implemented by importing the project as a Python library.
Later, you’ll be able to run this as a program by executing ``MTGDeckConverter``.

Contributing
------------

If you want to contribute, pull requests that fix issues or add additional input or output formats are welcome.
Just open a PR on GitHub to discuss the additions.

Running the tests
+++++++++++++++++

Running the unit test suite is integrated into setup.py.
So to run the tests, execute :code:`python3 setup.py test` from the git checkout root directory.

The tests require:

- `pytest <https://pypi.org/project/pytest/>`_
- `PyHamcrest <https://pypi.org/project/PyHamcrest/>`_
- `pyfakefs <https://pypi.org/project/pyfakefs/>`_

About
-----

Copyright (C) 2019, Thomas Hess

This program is licensed under the GNU GENERAL PUBLIC LICENSE Version 3.
See the LICENSE file for details.
