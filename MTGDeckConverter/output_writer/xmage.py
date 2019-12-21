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

import MTGDeckConverter.logger

logger = MTGDeckConverter.logger.get_logger(__name__)

deck_name_format_line = "NAME:{deck_name}\n"
main_deck_format_line = "{count} [{set}:{number}] {english_name}\n"
sideboard_format_line = "SB: {count} [{set}:{number}] {english_name}\n"


def write_deck_file(deck: Deck, output_path: Path):
    logger.info(f"Start writing deck {f'{deck.name} ' if deck.name else ''}to file {output_path}.")
    _fill_missing_information(deck)
    if deck.side_board and deck.commanders:
        logger.warning(
            "Writing a Commander deck with non-empty sideboard. As of December 2019, this is unsupported by XMage. "
            "All cards in the sideboard will be dropped!"
        )
    if deck.commanders:
        main_deck_lines, sideboard_deck_lines = _format_commander_deck(deck)
    else:
        main_deck_lines, sideboard_deck_lines = _format_non_commander_deck(deck)

    _write_deck_file(deck, output_path, main_deck_lines, sideboard_deck_lines)


def _format_commander_deck(deck):
    logger.debug("Found a Commander deck.")
    logger.debug("Placing all non-commander cards from the main board into the main board.")
    main_deck_lines = (
        main_deck_format_line.format(
            count=1,
            set=card.set_abbreviation,
            number=card.collector_number,
            english_name=card.english_name)
        for card in deck.main_deck
        if card not in deck.commanders
    )
    logger.debug("Placing all commander cards from the main board into the sideboard.")
    sideboard_deck_lines = (
        sideboard_format_line.format(
            count=1,
            set=card.set_abbreviation,
            number=card.collector_number,
            english_name=card.english_name)
        for card in deck.main_deck
        if card in deck.commanders
    )
    return main_deck_lines, sideboard_deck_lines


def _format_non_commander_deck(deck):
    logger.debug("Found a non-Commander deck.")
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
    return main_deck_lines, sideboard_deck_lines


def _write_deck_file(deck, output_path, main_deck_lines, sideboard_deck_lines):
    logger.debug("Opened output file.")
    with output_path.open("w", encoding="utf-8") as output_file:
        if deck.name:
            # Only write the name, if it is known.
            logger.debug("The deck has an associated name. Writing the name header.")
            output_file.write(deck_name_format_line.format(deck_name=deck.name))
        logger.debug("Writing the main deck list.")
        output_file.writelines(main_deck_lines)
        logger.debug("Writing the sideboard list.")
        output_file.writelines(sideboard_deck_lines)
        # Writing the LAYOUT section below the sideboard is currently not implemented.


def _fill_missing_information(deck: Deck):
    pass
