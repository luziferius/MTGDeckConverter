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


PRAGMA user_version(4);  -- 0.000.004
PRAGMA journal_mode('wal');
pragma foreign_keys(1);


CREATE TABLE Card_Set (
  Set_ID INTEGER PRIMARY KEY NOT NULL,
  English_Name TEXT NOT NULL UNIQUE,
  Abbreviation TEXT NOT NULL UNIQUE,
  Release_date DATE NOT NULL,
  Is_Paper_Set BOOLEAN NOT NULL DEFAULT(TRUE)

);


CREATE TABLE Card (
  -- An abstract M:TG card, which is identified by the Scryfall UUID. The English name is not unique for cards
  -- from the Unstable set (and maybe future silver bordered sets).
  Card_ID INTEGER PRIMARY KEY NOT NULL,
  English_Name TEXT NOT NULL,
  Card_Type TEXT NOT NULL,  -- The card type, like 'Creature'. Used by some formats to group cards by type.
  Scryfall_Oracle_ID UUID_TEXT NOT NULL UNIQUE CONSTRAINT 'UUID format' -- UUID_TEXT gives a TEXT type affinity.
   CHECK (
   -- Matches a hyphened UUID. Make sure that no duplicates caused by different formatting are possible.
   Scryfall_Oracle_ID GLOB
   '[a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9]-' ||
   '[a-f0-9][a-f0-9][a-f0-9][a-f0-9]-' ||
   '[a-f0-9][a-f0-9][a-f0-9][a-f0-9]-' ||
   '[a-f0-9][a-f0-9][a-f0-9][a-f0-9]-' ||
   '[a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9]')
);
CREATE INDEX CardEnglishName ON Card(English_Name);

CREATE TABLE Rarity (
  Rarity_ID INTEGER NOT NULL PRIMARY KEY,
  Code TEXT NOT NULL UNIQUE,
  Name TEXT NOT NULL UNIQUE
);

INSERT INTO Rarity (Rarity_ID, Code, Name) VALUES
  (1, 'L', 'Land'),
  (2, 'C', 'Common'),
  (3, 'U', 'Uncommon'),
  (4, 'R', 'Rare'),
  (5, 'M', 'Mythic'),
  (6, 'S', 'special'),
  (7, 'B', 'Bonus'),
  (8, 'T', 'Token');


CREATE TABLE Printing (
   Printing_ID INTEGER PRIMARY KEY NOT NULL,
   Card_ID INTEGER NOT NULL REFERENCES Card(Card_ID),
   Set_ID INTEGER NOT NULL REFERENCES Card_Set(Set_ID),
   Collector_Number INTEGER NOT NULL,  -- This MAY actually be a string, like '86a'. But it is an int most of the time.
   Rarity_ID INTEGER NOT NULL REFERENCES Rarity(Rarity_ID),
   Scryfall_Card_ID UUID_TEXT NOT NULL UNIQUE CONSTRAINT 'UUID format' -- UUID_TEXT gives a TEXT type affinity.
   CHECK (
    -- Matches a hyphened UUID. Make sure that no duplicates caused by different formatting are possible.
   Scryfall_Card_ID GLOB
   '[a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9]-' ||
   '[a-f0-9][a-f0-9][a-f0-9][a-f0-9]-' ||
   '[a-f0-9][a-f0-9][a-f0-9][a-f0-9]-' ||
   '[a-f0-9][a-f0-9][a-f0-9][a-f0-9]-' ||
   '[a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9]')
);

CREATE VIEW Printings_View AS
  SELECT Card.English_Name AS English_Name, Card_Set.English_Name AS Set_Name,
  Card_Set.Abbreviation AS Abbreviation, Card.Card_Type AS Card_Type, Printing.Collector_Number AS Collector_Number, Rarity.Name AS Rarity
  FROM Printing
  INNER JOIN Card_Set USING (Set_ID)
  INNER JOIN Card USING (Card_ID)
  INNER JOIN Rarity USING (Rarity_ID)
;
