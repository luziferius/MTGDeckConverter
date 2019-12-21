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
import MTGDeckConverter.logger

logger = MTGDeckConverter.logger.get_logger(__name__)


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


_CSV_DIALECT_NAME = "tappedout_net"
csv.register_dialect(_CSV_DIALECT_NAME, TappedOutDialect)
# Foiling indicators used in the CSV.
# "foil": Regular foil, "pre": Pre-release (and similar event) promo card. Always (?) foil with a golden date stamp.
csv_foil_indicators = {"foil", "pre"}


def parse_deck(csv_file_path: Path) -> MTGDeckConverter.model.Deck:
    logger.info(f"Parsing Tappedout.com CSV exported deck from location {csv_file_path}")
    deck = MTGDeckConverter.model.Deck()
    # These are the four categories/boards supported by TappedOut.
    card_categories = {
        "main": deck.add_to_main_deck,
        "side": deck.add_to_side_board,
        "maybe": deck.add_to_maybe_board,
        "acquire": deck.add_to_acquire_board,
    }
    for line in _read_lines_from_csv(csv_file_path):
        cards, is_commander = _parse_cards_from_line(line)
        for card in cards:
            # The Board column contains the category/board the card belongs to, so use it to look up the right setter.
            card_categories[line["Board"]](card, is_commander)
    return deck


def _read_lines_from_csv(csv_file_path: Path) -> typing.Generator[typing.Dict[str, str], None, None]:
    with csv_file_path.open("r", encoding="utf-8", newline="") as csv_file:
        yield from csv.DictReader(csv_file, dialect=_CSV_DIALECT_NAME)


def _parse_cards_from_line(line: typing.Dict[str, str]) -> typing.Tuple[typing.List[MTGDeckConverter.model.Card], bool]:
    """
    Parses the given CSV line into cards. If the quantity (field "Qty") is > 1,
    it returns the same card multiple times.
    """
    try:
        # TappedOut added the commander designation to the CSV export in December 2019.
        # Older (or previously compatible) exports may not have the Commander column.
        is_commander = line["Commander"] == "True"
    except KeyError:
        logger.warning(
            "Parsing old CSV export without commander designations. "
            "For better compatibility and conversion accuracy, please export the deck from TappedOut again.")
        is_commander = False
    try:
        language = line["Language"]
    except KeyError:
        # TappedOut fixed the typo in the CSV header in December 2019.
        # Older (or previously compatible) exports may still have the typo in the header line.
        language = line["Languange"]
    if not language:
        # Default to English if not set.
        language = "EN"

    card = MTGDeckConverter.model.Card(
        english_name=line["Name"],
        set_abbreviation=line["Printing"],
        language=language,
        foil=line["Foil"] in csv_foil_indicators,
        condition=line["Condition"],
    )
    quantity = int(line["Qty"])
    logger.debug(f"Parsed CSV line. Found {quantity} * '{card.english_name}'. Is Commander: {is_commander}")
    return [card] * quantity, is_commander
