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
import typing


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
    def __init__(self):
        self.main_deck: CardList = []
        self.side_board: CardList = []
        # The following two categories are used by TappedOut. Just store them in case of adding an output formatter
        # supporting it.
        self.maybe_board: CardList = []
        self.acquire_bord: CardList = []

        # A deck may have any number of cards in the command zone. This is empty for decks not using the zone.
        # A regular Commander or Brawl deck may have one or two commanders.
        # An Oathbreaker deck has two cards in this zone (a Planeswalker and an Instant or Sorcery signature spell).
        # This is supplemental information, the cards in this still have to be in the appropriate list above.
        # A deck may have a designated commander in the main deck and maybe multiple others in the maybe_board or
        # acquire_board. To keep this separated
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
            self.commanders.append(card)
