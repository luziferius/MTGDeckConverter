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

from dataclasses import dataclass
import itertools
import typing

from MTGDeckConverter.card_db.db import CardDatabase
import MTGDeckConverter.logger

logger = MTGDeckConverter.logger.get_logger(__name__)


@dataclass
class Card:
    """This is a single MTG card"""
    english_name: str = None
    set_abbreviation: str = None
    # Most cards have integer collector numbers, but some require further disambiguation in the form of appended letters
    # To support collector numbers like "86a", the collector number is handled as a string.
    collector_number: str = None
    # Returned by TappedOut.
    language: str = "EN"
    foil: bool = False
    condition: str = None


CardList = typing.List[Card]


class Deck:
    """
    An MTG deck. It consists of cards placed in a main deck and a side board.
    """
    def __init__(self, name: str = ""):
        logger.info(f"""Created an empty deck{f' with name "{name}"' if name else ''}.""")
        # Some formats allow specifying the deck name in the file. This can be used to write the deck name, if
        # supported by the output module.
        self.name = name
        self.main_deck: CardList = []
        self.side_board: CardList = []
        # The following two categories are used by TappedOut. Just store them in case of adding an output formatter
        # supporting it.
        self.maybe_board: CardList = []
        self.acquire_bord: CardList = []

        # A deck may have any number of cards in the command zone. This is empty for decks not using the zone.
        # A regular Commander or Brawl deck may have one or two commanders.
        # An Oathbreaker deck has two cards in this zone (a Planeswalker and an Instant or Sorcery signature spell).
        # This is supplemental information, the cards in this list still have to be in the appropriate list above.
        # A deck may have a designated commander in the main deck and maybe multiple others in the maybe_board or
        # acquire_board.
        self.commanders: CardList = []

    def add_to_main_deck(self, card: Card, is_commander: bool = False):
        self._add_to_deck(self.main_deck, card, is_commander)

    def add_to_side_board(self, card: Card, is_commander: bool = False):
        self._add_to_deck(self.side_board, card, is_commander)

    def add_to_maybe_board(self, card: Card, is_commander: bool = False):
        self._add_to_deck(self.maybe_board, card, is_commander)

    def add_to_acquire_board(self, card: Card, is_commander: bool = False):
        self._add_to_deck(self.acquire_bord, card, is_commander)

    def _add_to_deck(self, deck: CardList, card: Card, is_commander: bool = False):
        deck.append(card)
        if is_commander:
            logger.info(f"Adding designated Commander card to the Command zone: {card}")
            self.commanders.append(card)

    def fill_missing_information(self, card_db: CardDatabase):
        all_cards = itertools.chain(self.main_deck, self.side_board, self.maybe_board, self.acquire_bord)
        for card in all_cards:
            self._fill_information_for_card(card, card_db)

    @staticmethod
    def _fill_information_for_card(card: Card, card_db: CardDatabase):
        if card.english_name:
            if (not card.set_abbreviation and not card.collector_number) \
                    or (card.set_abbreviation and not card_db.is_set_abbreviation_known(card.set_abbreviation)):
                # Both are unknown or the set is not present in the database. Do a guess based on the English name.
                card.set_abbreviation, card.collector_number = card_db.get_card_set_and_number_for_name(
                    card.english_name
                )
            elif not card.collector_number:
                card.collector_number = card_db.get_collector_number_for_card_in_set(
                    card.english_name, card.set_abbreviation
                )
            elif not card.set_abbreviation:
                card.set_abbreviation = card_db.get_card_set_for_card_with_collector_number(
                    card.english_name, card.collector_number
                )
        else:
            # The English name is missing.
            # The card can be identified, if both the set and the collector number are known.
            if card.set_abbreviation and card.collector_number:
                card.english_name = card_db.get_english_name_for_card_in_card_set(
                    card.set_abbreviation, card.collector_number
                )
