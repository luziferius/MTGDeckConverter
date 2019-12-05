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

from pathlib import Path

from MTGDeckConverter.model import Deck

deck_name_format_line = "NAME:{deck_name}\n"
main_deck_format_line = "{count} [{set}:{number}] {english_name}\n"
sideboard_format_line = "SB: {count} [{set}:{number}] {english_name}\n"


def write_deck_file(deck: Deck, output_path: Path):
    _fill_missing_information(deck)
    main_deck_lines = (
        main_deck_format_line.format(
            count=1,
            set=card.set_abbreviation,
            number=card.collector_number,
            english_name=card.english_name)
        for card in deck.main_deck
    )
    sideboard_deck_lines = (
        sideboard_format_line.format(
            count=1,
            set=card.set_abbreviation,
            number=card.collector_number,
            english_name=card.english_name)
        for card in deck.side_board
    )
    with open(output_path, "w", encoding="utf-8") as output_file:
        if deck.name:
            # Only write the name, if it is known.
            output_file.write(deck_name_format_line.format(deck_name=deck.name))
        output_file.writelines(main_deck_lines)
        output_file.writelines(sideboard_deck_lines)
        # Writing the LAYOUT section below the sideboard is currently not implemented.


def _fill_missing_information(deck: Deck):
    pass
