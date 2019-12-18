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
import importlib.resources
import sqlite3
from typing import NamedTuple, Union
from pathlib import Path

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

    COMPATIBLE_SCHEMA_VERSIONS = CompatibleSchemaVersions(0, 2)

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
