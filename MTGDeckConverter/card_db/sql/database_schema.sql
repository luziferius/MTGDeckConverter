-- Copyright (C) 2019 Thomas Hess <thomas.hess@udo.edu>

-- This program is free software: you can redistribute it and/or modify
-- it under the terms of the GNU General Public License as published by
-- the Free Software Foundation, either version 3 of the License, or
-- (at your option) any later version.

-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU General Public License for more details.

-- You should have received a copy of the GNU General Public License
-- along with this program. If not, see <http://www.gnu.org/licenses/>.


PRAGMA user_version(1);  -- 0.000.001
PRAGMA journal_mode('wal');
pragma foreign_keys(1);


CREATE TABLE Card_Set (
  Set_ID INTEGER PRIMARY KEY NOT NULL,
  English_Name TEXT NOT NULL UNIQUE,
  Abbreviation TEXT NOT NULL UNIQUE
);


CREATE TABLE Card (
  -- An abstract M:TG card, which is identified by
  Card_ID INTEGER PRIMARY KEY NOT NULL,
  English_Name TEXT NOT NULL,
  Scryfall_Oracle_ID UUID_TEXT NOT NULL UNIQUE CONSTRAINT 'UUID format' -- UUID_TEXT gives a TEXT type affinity.
   CHECK (
   -- Matches a hyphened UUID. Make sure that no duplicates caused by different formatting are possible.
   Scryfall_Oracle_ID GLOB
   '[a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9]-' ||
   '[a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9]-' ||
   '[a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9]-' ||
   '[a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9]-' ||
   '[a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9]')
);
CREATE INDEX CardEnglishName ON Card(English_Name);


CREATE TABLE Printing (
   Printing_ID INTEGER PRIMARY KEY NOT NULL,
   Card_ID INTEGER NOT NULL REFERENCES Card(Card_ID),
   Set_ID INTEGER NOT NULL REFERENCES Card_Set(Set_ID),
   Collector_Number INTEGER NOT NULL,  -- This MAY actually be a string, like '86a'. But it is an int most of the time.
   Scryfall_Card_ID UUID_TEXT NOT NULL UNIQUE CONSTRAINT 'UUID format' -- UUID_TEXT gives a TEXT type affinity.
   CHECK (
    -- Matches a hyphened UUID. Make sure that no duplicates caused by different formatting are possible.
   Scryfall_Card_ID GLOB
   '[a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9]-' ||
   '[a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9]-' ||
   '[a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9]-' ||
   '[a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9]-' ||
   '[a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9]')
);
