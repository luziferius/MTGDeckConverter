# Copyright (C) 2019 Thomas Hess <thomas.hess@udo.edu>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""This module implements a parser for tappedout.com CSV exported decks."""

import csv
from pathlib import Path
import typing

import MTGDeckConverter.model


class TappedOutDialect(csv.Dialect):
    '''
    Specifies the CSV dialect used by TappedOut (http://tappedout.net/).
    The parameters were determined by inspecting exports. As a test case, a deck containing "Ach! Hans, Run!" was used.
    (Note that the actual card name contains both a comma and the quotation marks.)
    It is exported as """Ach! Hans, Run!""", therefore TappedOut uses the doublequote option.
    '''
    delimiter = ","
    quotechar = '"'
    doublequote = True
    skipinitialspace = False
    lineterminator = "\r\n"
    quoting = csv.QUOTE_MINIMAL


csv.register_dialect("tappedout_com", TappedOutDialect)


def parse_deck(csv_file_path: Path) -> MTGDeckConverter.model.Deck:
    deck = MTGDeckConverter.model.Deck()
    # These are the four categories/boards supported by TappedOut.
    card_categories = {
        "main": deck.add_to_main_deck,
        "side": deck.add_to_side_board,
        "maybe": deck.add_to_maybe_board,
        "acquire": deck.add_to_acquire_board,
    }
    for line in _read_lines_from_csv(csv_file_path):
        cards = _parse_cards_from_line(line)
        for card in cards:
            # Unfortunately, the CSV data does not contain the commander designation, therefore all cards are
            # marked as not being the commander, even if the deck has one or more.
            # The Board column contains the category/board the card belongs to, so use it to look up the right setter.
            card_categories[line["Board"]](card, False)
    return deck


def _read_lines_from_csv(csv_file_path: Path) -> typing.Generator[typing.Dict[str, str], None, None]:
    # Explicitly setting the field names, because the generated header contains a typo ("Languange").
    field_names = "Board,Qty,Name,Printing,Foil,Alter,Signed,Condition,Language".split(",")
    with open(csv_file_path, "r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file, fieldnames=field_names, dialect="tappedout_com")
        next(reader)  # Skip the header
        yield from reader


def _parse_cards_from_line(line: typing.Dict[str, str]) -> typing.List[MTGDeckConverter.model.Card]:
    """
    Parses the given CSV line into cards. If the quantity (field "Qty") is > 1,
    it returns the same card multiple times.
    """
    card = MTGDeckConverter.model.Card(
        english_name=line["Name"],
        set_abbreviation=line["Printing"],
        language="EN" if not line["Language"] else line["Language"],
        foil=bool(line["Foil"]),
        condition=line["Condition"],
    )
    return [card] * int(line["Qty"])
