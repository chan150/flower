# Copyright 2024 Flower Labs GmbH. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Utility to validate the `flower.toml` file."""

import importlib
import os
from typing import Any, Dict, List, Optional, Tuple

import tomli


def load_flower_toml(path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Load flower.toml and return as dict."""
    if path is None:
        cur_dir = os.getcwd()
        toml_path = os.path.join(cur_dir, "flower.toml")
    else:
        toml_path = path

    if not os.path.isfile(toml_path):
        return None

    with open(toml_path, encoding="utf-8") as toml_file:
        data = tomli.loads(toml_file.read())
        return data


def validate_flower_toml_fields(
    config: Dict[str, Any]
) -> Tuple[bool, List[str], List[str]]:
    """Validate flower.toml fields."""
    errors = []
    warnings = []

    if "project" not in config:
        errors.append("Missing [project] section")
    else:
        if "name" not in config["project"]:
            errors.append('Property "name" missing in [project]')
        if "version" not in config["project"]:
            errors.append('Property "version" missing in [project]')
        if "description" not in config["project"]:
            warnings.append('Recommended property "description" missing in [project]')
        if "license" not in config["project"]:
            warnings.append('Recommended property "license" missing in [project]')
        if "authors" not in config["project"]:
            warnings.append('Recommended property "authors" missing in [project]')

    if "flower" not in config:
        errors.append("Missing [flower] section")
    elif "components" not in config["flower"]:
        errors.append("Missing [flower.components] section")
    else:
        if "serverapp" not in config["flower"]["components"]:
            errors.append('Property "serverapp" missing in [flower.components]')
        if "clientapp" not in config["flower"]["components"]:
            errors.append('Property "clientapp" missing in [flower.components]')

    return len(errors) == 0, errors, warnings


def validate_object_reference(ref: str) -> Tuple[bool, Optional[str]]:
    """Validate object reference.

    Returns
    -------
    Tuple[bool, Optional[str]]
        A boolean indicating whether an object reference is valid and
        the reason why it might not be.
    """
    module_str, _, attributes_str = ref.partition(":")
    if not module_str:
        return (
            False,
            f"Missing module in {ref}",
        )
    if not attributes_str:
        return (
            False,
            f"Missing attribute in {ref}",
        )

    # Load module
    try:
        module = importlib.import_module(module_str)
    except ModuleNotFoundError:
        return False, f"Unable to load module {module_str}"

    # Recursively load attribute
    attribute = module
    try:
        for attribute_str in attributes_str.split("."):
            attribute = getattr(attribute, attribute_str)
    except AttributeError:
        return (
            False,
            f"Unable to load attribute {attributes_str} from module {module_str}",
        )

    return (True, None)


def validate_flower_toml(config: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """Validate flower.toml."""
    is_valid, errors, warnings = validate_flower_toml_fields(config)

    if not is_valid:
        return False, errors, warnings

    # Validate serverapp
    is_valid, reason = validate_object_reference(
        config["flower"]["components"]["serverapp"]
    )
    if not is_valid and isinstance(reason, str):
        return False, [reason], []

    # Validate clientapp
    is_valid, reason = validate_object_reference(
        config["flower"]["components"]["clientapp"]
    )

    if not is_valid and isinstance(reason, str):
        return False, [reason], []

    return True, [], []


def apply_defaults(
    config: Dict[str, Any],
    defaults: Dict[str, Any],
) -> Dict[str, Any]:
    """Apply defaults to config."""
    for key in defaults:
        if key in config:
            if isinstance(config[key], dict) and isinstance(defaults[key], dict):
                apply_defaults(config[key], defaults[key])
        else:
            config[key] = defaults[key]
    return config
