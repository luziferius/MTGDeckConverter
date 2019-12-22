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

import re
from pathlib import Path

from .db import CardDatabase
from .natsort import natural_sorted

from MTGDeckConverter.logger import get_logger

logger = get_logger(__name__)

# Simple patch naming schema: <from_version>/<to_version>.sql, where both from_version and to_version use
# semantic versioning (http://semver.org/spec/v2.0.0.html) and
# are built like M.m.P, where M, m, P are non-negative integer numbers.
# M is the major version, m is the minor version and P is the patch version.
_PATCH_SEMVER_SCHEMA = r"(([0-9]|[1-9][0-9]+)\.){2}([0-9]|[1-9][0-9]+)"
_PATCH_FILE_SCHEMA = _PATCH_SEMVER_SCHEMA + r"\.sql"

_PATCH_LIST_PATH = Path(__file__).resolve().absolute().joinpath("sql", "patches")


def update_database_schema(db: CardDatabase):
    """
    Update the database schema to the latest version.
    Implementation: the sql/patches folder MAY contain folders that, if present MUST following the semantic versioning
    schema. Each of those folders is interpreted as a source (or "from") version for patches. Each of those folders
    SHOULD contain at least one patch file following the naming schema "<semantic version>.sql" and is interpreted as
    a target (or "to") version. Each "from" folder MAY contain multiple patches to different versions. If multiple
    patches are present, the patch that patches to the highest possible version is used. This can be used to skip
    intermediate patch steps by providing a combined patch script.
    :return:
    """
    current_version = db.get_current_schema_version()
    logger.info(f"Initial database schema version: {version_str(current_version)}")
    number_applied_patches = sum(
        try_apply_patch_folder(db, patch_folder)
        for patch_folder
        in natural_sorted(p.name for p in _PATCH_LIST_PATH.glob("*")))
    logger.info(f"Number of applied patches: {number_applied_patches}")

    current_version = db.get_current_schema_version()
    min_version = db.COMPATIBLE_SCHEMA_VERSIONS.inclusive_min
    max_version = db.COMPATIBLE_SCHEMA_VERSIONS.exclusive_max
    if not min_version <= current_version < max_version:
        error_msg = f"Available patches did not update the database to a usable schema version. " \
                    f"Expected compatible version between {version_str(min_version)} and " \
                    f"{version_str(max_version)}, got {version_str(current_version)}."
        logger.error(error_msg)
        raise ValueError(error_msg)
    else:
        db.db.commit()
        logger.info(f"Current database schema version: {version_str(current_version)}")


def try_apply_patch_folder(db: CardDatabase, patch_folder: str) -> int:
    """
    Try to apply a patch from version equal to patch_folder to a later version. The patch folder may contain
    summary patches, so that not every minor patch has to be applied in order. This function will try to patch to
    the highest target version patchable using this folder.
    :param db: The database to operate on.
    :param patch_folder: Folder containing patches
    :return:
    """
    validate_patch_folder(patch_folder)
    current_version = db.get_current_schema_version()
    src_version = parse_patch_name(patch_folder)
    if current_version < src_version:
        error_msg = f'Patch for version "{patch_folder}" cannot be applied to a database with version ' \
                    f'{version_str(src_version)}. \nMaybe missing intermediate patches?'
        logger.error(error_msg)
        raise ValueError(error_msg)
    elif current_version > src_version:
        # Already applied
        logger.info(f"Skipping already applied patch for version {version_str(src_version)}")
        return 0
    current_patch_folder = _PATCH_LIST_PATH.joinpath(patch_folder)
    sorted_patch_names = natural_sorted((p.name for p in current_patch_folder.glob("*.sql")), reverse=True)
    if sorted_patch_names:
        best_patch_match = sorted_patch_names[0]
        logger.debug(f"Available patches: {sorted_patch_names}, chosen best patch {best_patch_match}")
        try_apply_patch(db, current_patch_folder.joinpath(best_patch_match))
        return 1
    else:
        # The current patch folder is empty, skipping. This means that we cannot patch away from the current version.
        # If the current src folder and all existing higher src folders are empty, and the current schema version
        # is usable, this will work. If any higher src folder has patches, the patching will fail because of a missing
        # intermediate patch.
        logger.warning(
            f"Found no patch files for current patch level {patch_folder}. If the whole patch process ends "
            f"successfully, this message is harmless. Otherwise it means that a required, intermediate patch is "
            f"missing.")
        return 0


def try_apply_patch(db: CardDatabase, patch: Path):
    """
    Try to apply a patch. This either works, or raises a ValueError.
    :param db: The database to operate on.
    :param patch:
    :return:
    """
    validate_patch_name(patch.name)
    target_version = parse_patch_name(patch.name)
    patch_version_string = strip_end(patch.name, ".sql")
    logger.info(f"Try to apply patch from version {patch.parent.name} to {patch_version_string} …")
    apply_patch(db, patch)

    current_version = db.get_current_schema_version()
    if current_version != target_version:
        error_msg = f"Patch from {str(patch.parent.name)} to {patch_version_string} did not set schema version " \
                    f"properly. Expected {version_str(target_version)}, got {version_str(current_version)}."
        logger.error(error_msg)
        raise ValueError(error_msg)
    else:
        logger.info("Patch applied successfully.")


def validate_patch_folder(patch_folder: str):
    if not re.fullmatch(_PATCH_SEMVER_SCHEMA, patch_folder):
        error_msg = f"Invalid patch folder name: {patch_folder}"
        logger.error(error_msg)
        raise ValueError(error_msg)


def validate_patch_name(patch_name: str):
    if not re.fullmatch(_PATCH_FILE_SCHEMA, patch_name):
        error_msg = f"Invalid patch file name: {patch_name}"
        logger.error(error_msg)
        raise ValueError(error_msg)


def parse_patch_name(patch_name: str) -> int:
    """
    Convert a 3-part semantic versioning string into a single integer. Due to restrictions in the sqlite database,
    the string has to be converted into a single 32 bit integer. Therefore Minor and Patch version support only 3
    digits.
    Supports version strings from "0.0.0" up to "9999.999.999"
    :param patch_name: A version string like "1.2.3"
    """
    patch_name = strip_end(patch_name, ".sql")
    parts = [int(number_part) for number_part in patch_name.split(".")]
    parts.reverse()
    result = sum(1000**i*parts[i] for i in range(0, len(parts)))
    logger.debug(f"Parsed patch name: {patch_name}, result: {result}")
    return result


def apply_patch(db: CardDatabase, patch_file_path: Path):
    """Apply a patch file by reading an SQL file and execute the content."""

    logger.debug(f'About to execute SQL script from patch file located at "{patch_file_path}".')
    db.db.executescript(patch_file_path.read_text())
    logger.debug("Success.")


def strip_end(text, suffix):
    """
    Remove suffix from string text, if present. Returns the text unmodified, if it does not end with suffix.
    :param text:
    :param suffix:
    :return:
    """
    if not text.endswith(suffix):
        return text
    return text[:len(text)-len(suffix)]


def version_str(version: int) -> str:
    """
    Converts the internally used integer version into a 3-part semantic versioning string.
    :param version:
    :return:
    """
    logger.debug(f"Converting version number {version} to a version string.")
    parts = []
    while version != 0:
        parts.append(str(version % 1000))
        version //= 1000
    while len(parts) < 3:
        parts.append("0")
    result = ".".join(reversed(parts))
    logger.debug(f"Result: {result}")
    return result
