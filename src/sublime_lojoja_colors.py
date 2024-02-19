"""
sublime_lojoja_colors

Validate and build defined color schemes.
"""

from __future__ import annotations
import json
from pathlib import Path
import re
import typing as t
import typing_extensions as te

from pydantic import BaseModel, Field, StringConstraints, model_validator, field_validator, ValidationInfo


NeStr: t.TypeAlias = te.Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

PROJECT_DIR = Path(__file__).parents[1]
DATA_DIR = PROJECT_DIR / "src/data"
CONFIG_FILE = DATA_DIR / "config.json"
CONFIG_SCHEMA_FILE = DATA_DIR / "config.schema.json"
TEMPLATE_FILE = DATA_DIR / "template.sublime-color-scheme"


class Config(BaseModel):
    """Color scheme configuration file.

    :attribute palettes: The color scheme palettes, keyed by their name.
    :attribute schemes: A list of color scheme definitions.
    """

    palettes: dict[NeStr, Palette] = {}
    schemes: list[Scheme] = []

    @field_validator("schemes", mode="after")
    @classmethod
    def validate_scheme_palette_references(cls, v: list[Scheme], values: ValidationInfo) -> list[Scheme]:
        """Validate palette references in a color scheme.

        :param v: The value to validate.
        :param values: The previously validated data.
        :raises ValueError: When the scheme references an unknown palette.
        """
        known_palettes: dict[NeStr, Palette] = values.data.get("palettes", {})
        for scheme in v:
            unknown_palettes = [p for p in scheme.palettes if p not in known_palettes]
            if unknown_palettes:
                raise ValueError(f"{scheme.name} scheme references unknown palette(s): {', '.join(unknown_palettes)}")
        return v


class Palette(BaseModel):
    """A color scheme palette.

    :attribute globals: Sublime color scheme `global` parameters.
    :attribute variables: Sublime color scheme `variable` parameters.
    """

    globals: dict[NeStr, NeStr]
    variables: dict[NeStr, NeStr]


class Scheme(BaseModel):
    """A color scheme definition.

    :attribute name: The color scheme name.
    :attribute author: The color schemes author.
    :attribute palettes: The names of palettes to include in this color scheme.
    """

    name: NeStr
    author: NeStr
    palettes: list[NeStr] = Field(..., min_length=1)


class SublimeColorScheme(BaseModel):
    """A Sublime Text color scheme.

    A constructed color scheme built from a `SublimeColorSchemeTemplate` and one or more `Palette`s.

    :attribute name: The color scheme name.
    :attribute author: The color scheme author.
    :attribute globals: Global parameters for the color scheme.
    :attribute variables: Variable parameters for the color scheme.
    :attribute rules: A list of rules for the color scheme.
    """

    name: NeStr
    author: NeStr
    variables: dict[NeStr, NeStr] = {}
    globals: dict[NeStr, NeStr] = Field(..., min_length=1)
    rules: list[dict[NeStr, NeStr]] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_variable_references(self) -> t.Self:
        """Validate variable references match a known variable name in the color scheme.

        :param v: The value to validate.
        :param values: The previously validated data.
        :raises ValueError: When an unknown variable is referenced.
        """
        var_pattern = re.compile(r"\bvar\((\w+)\)\B")

        for model_data in [self.variables, self.globals, self.rules]:
            for idx, data in enumerate([model_data] if isinstance(model_data, dict) else model_data):
                error_prefix = f"item {idx} " if isinstance(model_data, list) else ""
                for key, value in data.items():
                    var_refs = re.findall(var_pattern, value)
                    for var in var_refs:
                        if var not in self.variables:
                            raise ValueError(f"{error_prefix}'{key}' references unknown variable '{var}'")
        return self


class SublimeColorSchemeTemplate(BaseModel):
    """A Sublime Text color scheme template.

    A template is a partial representation of a `SublimeColorScheme` with common directives. The model has relaxed
    validation compared to a `SublimeColorScheme` because missing/incomplete values will be provided by a color scheme
    definition.

    :attribute name: The color scheme name.
    :attribute author: The color scheme author.
    :attribute globals: Global parameters for the color scheme.
    :attribute variables: Variable parameters for the color scheme.
    :attribute rules: A list of rules for the color scheme.
    """

    name: str = ""
    author: str = ""
    globals: dict[NeStr, NeStr] = {}
    variables: dict[NeStr, NeStr] = {}
    rules: list[dict[NeStr, NeStr]] = []


def build(validate_only: bool = False) -> None:
    """Build color schemes.

    :param validate_only: Whether to validate color schemes without writing them to disk.
    """
    config = Config.model_validate_json(CONFIG_FILE.read_text(encoding="utf8"))
    template = SublimeColorSchemeTemplate.model_validate_json(TEMPLATE_FILE.read_text(encoding="utf8"))

    schemes = []

    for scheme in config.schemes:
        schemes.append(construct_color_scheme(scheme, template, config.palettes))

    if validate_only:
        print(f"Validated {len(schemes)} color scheme(s)")
    else:
        for scheme in schemes:
            save_color_scheme(scheme)
        print(f"Created {len(schemes)} color scheme(s)")


def config_schema() -> None:
    """Generate a JSON schema for the configuration model."""
    schema = json.dumps(Config.model_json_schema(), indent=2)

    try:
        CONFIG_SCHEMA_FILE.write_text(schema, encoding="utf8")
    except OSError as exc:
        raise OSError(f"Failed to write configuration JSON schema {CONFIG_SCHEMA_FILE.name}") from exc


def construct_color_scheme(
    scheme: Scheme, template: SublimeColorSchemeTemplate, palettes: dict[NeStr, Palette]
) -> SublimeColorScheme:
    """Construct a color scheme from it's definition.

    :param scheme: The color scheme definition.
    :param palettes: The available color palettes.
    """
    data = {
        "name": scheme.name,
        "author": scheme.author,
        "variables": template.variables.copy(),
        "globals": template.globals.copy(),
        "rules": template.rules,
    }

    for palette in scheme.palettes:
        data["variables"].update(palettes[palette].variables)
        data["globals"].update(palettes[palette].globals)

    return SublimeColorScheme(**data)


def save_color_scheme(scheme: SublimeColorScheme) -> None:
    """Save a color scheme to disk.

    :param scheme: The color scheme to save.
    :raises OSError: When the color scheme file cannot be written.
    """
    file = PROJECT_DIR / f"{scheme.name}.sublime-color-scheme"

    try:
        file.write_text(scheme.model_dump_json(indent=2), encoding="utf8")
    except OSError as exc:
        raise OSError(f"Failed to write color scheme file: {file.name}") from exc


def validate() -> None:
    """Validate color schemes."""
    build(validate_only=True)
