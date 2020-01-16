# Copyright (C) 2017-2019 Thomas Hess <thomas.hess@udo.edu>

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

import atexit
import datetime
from http import HTTPStatus
import importlib.resources
import sqlite3
from typing import NamedTuple, Union, List, Tuple
from pathlib import Path

import requests

from MTGDeckConverter.logger import get_logger

logger = get_logger(__name__)


class CompatibleSchemaVersions(NamedTuple):
    inclusive_min: int
    exclusive_max: int


class CardDatabase:

    """
    This class maintains an offline database with M:TG card data.
    The database has to be populated one time to gather all relevant information about the existing cards.

    It is used to fill in missing, but required information bits. For example the collector number,
    in case an output writer (e.g. XMage) requires data
    that is not present in the parsed input (e.g. tappedout.com CSV exports).
    """
    # TODO: Implement updating the present data when new sets are released.
    #       Either implement an update function or simply drop the content
    #       and re-download everything.

    COMPATIBLE_SCHEMA_VERSIONS = CompatibleSchemaVersions(4, 5)

    def __init__(self, database_path: Union[str, Path], do_validate_schema: bool = True):
        logger.info(f"About to open database: {database_path}, validating schema: {do_validate_schema}")
        if isinstance(database_path, Path):
            database_path = str(database_path)
        self.db = sqlite3.connect(database=database_path)
        atexit.register(self._close_db)
        self.db.row_factory = sqlite3.Row
        self._create_schema_if_not_present()
        if do_validate_schema:
            self._validate_schema_version()
            logger.info("Opened database in checked mode and schema version checks passed.")
        else:
            logger.info("Opened database in unchecked mode. No schema version checks were performed.")

    def _validate_schema_version(self):
        current_db_schema_version = self.get_current_schema_version()
        if current_db_schema_version < self.COMPATIBLE_SCHEMA_VERSIONS.inclusive_min:
            error_msg = f"Schema version mismatch. Expected at least " \
                        f"{self.COMPATIBLE_SCHEMA_VERSIONS.inclusive_min}, but got {current_db_schema_version}. " \
                        f"Did you update the program? You need to migrate your database."
            logger.error(error_msg)
            raise ConnectionAbortedError(error_msg)
        if current_db_schema_version >= self.COMPATIBLE_SCHEMA_VERSIONS.exclusive_max:
            error_msg = f"Schema version too high. Expected a version below " \
                        f"{self.COMPATIBLE_SCHEMA_VERSIONS.exclusive_max}, but got {current_db_schema_version}. " \
                        f"Have you performed a migration using a newer version of the program? " \
                        f"Automatic downgrades are not supported."
            logger.error(error_msg)
            raise ConnectionAbortedError(error_msg)
        self.db.execute("PRAGMA foreign_keys (1)")

    def _create_schema_if_not_present(self):
        if self.get_current_schema_version() == 0:
            logger.info("Opened an empty database, creating database schema…")
            from . import sql
            schema = importlib.resources.read_text(sql, "database_schema.sql")
            self.db.executescript(schema)
            self.db.commit()
            self.db.execute("BEGIN TRANSACTION")
            logger.debug("Written schema")

    def get_current_schema_version(self) -> int:
        return self.db.execute("PRAGMA user_version").fetchall()[0][0]

    def _close_db(self):
        if self.db is None:
            error_msg = "Invalid state: close_db() called twice!"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        else:
            self.db.rollback()
            self.db.close()
            self.db = None

    def is_database_populated(self) -> bool:
        result = self.db.execute(
            "SELECT EXISTS( "
            "SELECT * "
            "FROM Printing)").fetchone()[0]
        return bool(result)

    def populate_database(self, path_to_data: Path = None):
        if self.is_database_populated():
            logger.warning("The database already contains data. Skipping the population process.")
            return
        card_data_list = _request_scryfall_card_data(path_to_data)
        self.db.rollback()
        cursor = self.db.cursor()
        cursor.execute("BEGIN TRANSACTION")
        try:
            for card in card_data_list:
                oracle_id = card["oracle_id"]
                set_abbr = card["set"]
                if not bool(cursor.execute(
                        "SELECT EXISTS( "
                        "SELECT * "
                        "FROM Card "
                        "WHERE Scryfall_Oracle_ID = ?)", (oracle_id,)).fetchone()[0]):
                    # TODO: This may not work and may require further normalization.
                    card_type = card["type_line"].split(" — ")[0]
                    cursor.execute("INSERT INTO Card (English_Name, Card_Type, Scryfall_Oracle_ID) "
                                   "VALUES (?, ?, ?)", (card["name"], card_type, oracle_id))
                if not bool(cursor.execute(
                        "SELECT EXISTS( "
                        "SELECT * "
                        "FROM Card_Set "
                        "WHERE Abbreviation = ?)", (set_abbr,)).fetchone()[0]):
                    release_date = datetime.date.fromisoformat(card["released_at"])
                    cursor.execute("INSERT INTO Card_Set (English_Name, Abbreviation, Release_date) "
                                   "VALUES (?, ?, ?)", (card["set_name"], set_abbr, release_date))

                rarity = "Land" \
                    if card["name"] in ("Plains", "Island", "Swamp", "Mountain", "Forest") \
                    else card["rarity"].title()
                # Do the table ID lookups by the unique set abbreviation and oracle id

                # This query joins unconnected relations and filters for the single tuple that contains the required
                # unique IDs
                cursor.execute(
                    "INSERT INTO Printing (Card_ID, Set_ID, Rarity_ID, Collector_Number, Scryfall_Card_ID) "
                    "SELECT Card_ID, Set_ID, Rarity.Rarity_ID, ?, ? "
                    "FROM Rarity "
                    "INNER JOIN Card_Set "
                    "INNER JOIN Card "
                    "WHERE Card_Set.Abbreviation = ? "
                    "AND Card.Scryfall_Oracle_ID = ? "
                    "AND Rarity.Name = ?",
                    (card["collector_number"], card["id"], set_abbr, oracle_id, rarity))
        except Exception as e:
            self.db.rollback()
            raise e
        else:
            self.db.commit()

    def get_card_set_and_number_for_name(self, english_name: str) -> Tuple[str, str]:
        found_cards = self.db.execute(
            "SELECT Abbreviation, Collector_Number "
            "FROM Printings_View "
            "WHERE English_Name = ?",
            (english_name,)
        ).fetchall()
        if found_cards:
            return found_cards[0]["Abbreviation"], found_cards[0]["Collector_Number"]
        else:
            raise ValueError(f'Card with name "{english_name}" not found')

    def get_collector_number_for_card_in_set(self, english_name: str, set_abbreviation: str) -> str:
        found_cards = self.db.execute(
            "SELECT Collector_Number "
            "FROM Printings_View "
            "WHERE English_Name = ? "
            "AND Abbreviation = ?",
            (english_name, set_abbreviation.lower())
        ).fetchall()
        if found_cards:
            return found_cards[0]["Collector_Number"]
        else:
            raise ValueError(f'Card with name "{english_name}" not found in set "{set_abbreviation}".')

    def get_card_set_for_card_with_collector_number(self, english_name: str, collector_number: str) -> str:
        found_cards = self.db.execute(
            "SELECT Abbreviation "
            "FROM Printings_View "
            "WHERE English_Name = ? "
            "AND Collector_Number = ?",
            (english_name, collector_number.lower())
        ).fetchall()
        if found_cards:
            return found_cards[0]["Abbreviation"]
        else:
            raise ValueError(
                f'No set found for card with name "{english_name}" and collector’s number "{collector_number}".'
            )

    def get_english_name_for_card_in_card_set(self, set_abbreviation: str, collector_number: str) -> str:
        found_cards = self.db.execute(
            "SELECT English_Name "
            "FROM Printings_View "
            "WHERE Abbreviation = ? "
            "AND Collector_Number = ?",
            (set_abbreviation.lower(), collector_number.lower())
        ).fetchall()
        if found_cards:
            return found_cards[0]["English_Name"]
        else:
            raise ValueError(
                f'Set "{set_abbreviation}" does not have a card with collector’s number "{collector_number}".'
            )

    def is_set_abbreviation_known(self, set_abbreviation: str) -> bool:
        """
        Check, if the set abbreviation is known.
        Especially with promotional sets, the set abbreviations used differ between different sources.
        If the set abbreviation is unknown, exact printing can’t be determined.
        """
        is_known = bool(self.db.execute(
            "SELECT EXISTS ( "
            "SELECT * "
            "FROM Card_Set "
            "WHERE Abbreviation = ?)",
            (set_abbreviation,)
        ).fetchone()[0])
        return is_known


def _request_scryfall_card_data(path_to_data: Path = None) -> List[dict]:
    """
    Use the Scryfall API bulk data end point to download the card data.
    See the API documentation: https://scryfall.com/docs/api/bulk-data
    The returned list contains > 50000 card entries (as of December 2019).

    If path_to_data is given, the file content will be used as a substitute.
    This is factored out into a static function used by the CardDatabase class to aid testing.
    Mock this function for unit tests that should not access the online API.

    """
    if path_to_data is None:
        logger.info("About to request card data from the Scryfall bulk data API.")
        card_data_request = requests.get("https://archive.scryfall.com/json/scryfall-default-cards.json")
        if card_data_request.status_code != HTTPStatus.OK:
            error_msg = f"Request to download the card data failed with status code {card_data_request.status_code}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        card_data_list: List[dict] = card_data_request.json()
        logger.info("Requested the card data from the Scryfall bulk data API end point.")
    else:
        logger.info(f'Path to a Scryfall API data dump given. Loading data from "{path_to_data}".')
        import json
        card_data_list = json.loads(path_to_data.read_text())
    return card_data_list
