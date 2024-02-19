# pylint: disable=missing-module-docstring,missing-function-docstring

from contextlib import nullcontext as does_not_raise
import json
from pathlib import Path

from pydantic import ValidationError
import pytest
from pytest_mock import MockerFixture


from sublime_lojoja_colors import (
    Config,
    Palette,
    Scheme,
    SublimeColorScheme,
    SublimeColorSchemeTemplate,
    config_schema,
    construct_color_scheme,
    save_color_scheme,
    build,
    validate,
)


@pytest.mark.parametrize("palette_name", ["", " ", "x"])
def test_config_palette_name(palette_name: str):
    context = does_not_raise() if palette_name.strip() else pytest.raises(ValidationError)
    with context:
        Config(palettes={palette_name: Palette(globals={}, variables={})}, schemes=[])


@pytest.mark.parametrize("ref_name", ["x", "y"])
@pytest.mark.parametrize("palette_name", "x")
def test_config_scheme_palette_reference_validation(palette_name: str, ref_name: str):
    context = does_not_raise() if ref_name == palette_name else pytest.raises(ValidationError)
    with context:
        Config(
            palettes={palette_name: Palette(globals={}, variables={})},
            schemes=[Scheme(name="x", author="x", palettes=[ref_name])],
        )


@pytest.mark.parametrize("value", ["", " ", "test"])
@pytest.mark.parametrize("target", ["key", "value"])
@pytest.mark.parametrize("attr", ["globals", "variables"])
def test_palette_globals_variables(attr: str, target: str, value: str):
    context = does_not_raise() if value.strip() else pytest.raises(ValidationError)
    data = {value if target == "key" else "x": value if target == "value" else "x"}
    with context:
        Palette(globals=data if attr == "globals" else {}, variables=data if attr == "variables" else {})


@pytest.mark.parametrize("value", ["", " ", "x"])
@pytest.mark.parametrize("attr", ["name", "author"])
def test_scheme_name_author(attr: str, value: str):
    context = does_not_raise() if value.strip() else pytest.raises(ValidationError)
    with context:
        Scheme(name=value if attr == "name" else "x", author=value if attr == "author" else "x", palettes=["x"])


@pytest.mark.parametrize("value", ["", " ", "x"])
@pytest.mark.parametrize("count", [0, 1])
def test_scheme_palettes(count: int, value: str):
    context = does_not_raise() if count > 0 and value.strip() else pytest.raises(ValidationError)
    with context:
        Scheme(name="x", author="x", palettes=[value * count])


@pytest.mark.parametrize("value", ["", " ", "x"])
@pytest.mark.parametrize("attr", ["name", "author"])
def test_sublime_color_scheme_name_author(attr: str, value: str):
    context = does_not_raise() if value.strip() else pytest.raises(ValidationError)
    with context:
        SublimeColorScheme(
            name=value if attr == "name" else "x",
            author=value if attr == "author" else "x",
            variables={},
            globals={"x": "y"},
            rules=[{"x": "y"}],
        )


@pytest.mark.parametrize("value", ["", " ", "test"])
@pytest.mark.parametrize("target", ["key", "value"])
@pytest.mark.parametrize("attr", ["globals", "variables"])
def test_sublime_color_scheme_globals_variables(attr: str, target: str, value: str):
    context = does_not_raise() if value.strip() else pytest.raises(ValidationError)
    data = {value if target == "key" else "x": value if target == "value" else "x"}
    with context:
        SublimeColorScheme(
            name="x",
            author="x",
            globals=data if attr == "globals" else {"x": "y"},
            variables=data if attr == "variables" else {},
            rules=[{"x": "y"}],
        )


@pytest.mark.parametrize("value", ["", " ", "test"])
@pytest.mark.parametrize("target", ["key", "value"])
@pytest.mark.parametrize("count", [0, 1])
def test_sublime_color_scheme_rules(count: int, target: str, value: str):
    context = does_not_raise() if count > 0 and value.strip() else pytest.raises(ValidationError)
    data = {value if target == "key" else "x": value if target == "value" else "x"}
    with context:
        SublimeColorScheme(name="x", author="x", globals={"x": "y"}, variables={}, rules=[data] if count > 0 else [])


@pytest.mark.parametrize("var_ref_name", ["varname", "x"])
@pytest.mark.parametrize("var_name", "varname")
@pytest.mark.parametrize("attr", ["variables", "globals", "rules"])
def test_sublime_color_scheme_validate_variable_references(attr: str, var_name: str, var_ref_name: str):
    context = does_not_raise() if var_ref_name == var_name else pytest.raises(ValidationError)
    data_value = f"var({var_name}) var({var_ref_name})"
    with context:
        SublimeColorScheme(
            name="x",
            author="x",
            globals={"x": data_value if attr == "globals" else "y"},
            variables={var_name: "y", "othervarname": data_value if attr == "variables" else "y"},
            rules=[{"x": data_value if attr == "rules" else "y"}],
        )


@pytest.mark.parametrize("value", ["", " ", "x"])
@pytest.mark.parametrize("attr", ["name", "author"])
def test_sublime_color_scheme_template_name_author(attr: str, value: str):
    model = SublimeColorSchemeTemplate(**{attr: value})  # type: ignore
    assert getattr(model, attr) == value


@pytest.mark.parametrize("value", ["", " ", "test"])
@pytest.mark.parametrize("target", ["key", "value"])
@pytest.mark.parametrize("attr", ["globals", "variables"])
def test_sublime_color_scheme_template_globals_variables(attr: str, target: str, value: str):
    context = does_not_raise() if value.strip() else pytest.raises(ValidationError)
    data = {value if target == "key" else "x": value if target == "value" else "x"}
    with context:
        SublimeColorSchemeTemplate(
            name="x",
            author="x",
            globals=data if attr == "globals" else {},
            variables=data if attr == "variables" else {},
            rules=[],
        )


@pytest.mark.parametrize("value", ["", " ", "test"])
@pytest.mark.parametrize("target", ["key", "value"])
@pytest.mark.parametrize("count", [0, 1])
def test_sublime_color_scheme_template_rules(count: int, target: str, value: str):
    context = does_not_raise() if count == 0 or value.strip() else pytest.raises(ValidationError)
    data = {value if target == "key" else "x": value if target == "value" else "x"}
    with context:
        SublimeColorSchemeTemplate(name="x", author="x", globals={}, variables={}, rules=[data] if count > 0 else [])


@pytest.mark.parametrize("scheme_count", [1, 2])
@pytest.mark.parametrize("validate_only", [True, False])
def test_build(
    capsys: pytest.CaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    validate_only: bool,
    scheme_count: int,
):
    monkeypatch.setattr("sublime_lojoja_colors.PROJECT_DIR", tmp_path)

    config_data = {
        "schemes": [{"name": "x", "author": "x", "palettes": ["x"]}],
        "palettes": {"x": {"globals": {"x": "y"}, "variables": {"x": "y"}}},
    }
    if scheme_count > 1:
        config_data["schemes"].append({"name": "y", "author": "y", "palettes": ["x"]})

    test_config_file = tmp_path / "config.json"
    test_config_file.write_text(json.dumps(config_data), encoding="utf8")
    monkeypatch.setattr("sublime_lojoja_colors.CONFIG_FILE", test_config_file)

    template_data = {"name": "", "author": "", "variables": {}, "globals": {}, "rules": [{"x": "y"}]}
    test_template_file = tmp_path / "template.sublime-color-scheme"
    test_template_file.write_text(json.dumps(template_data), encoding="utf8")
    monkeypatch.setattr("sublime_lojoja_colors.TEMPLATE_FILE", test_template_file)

    build(validate_only=validate_only)

    assert (
        capsys.readouterr().out
        == f"{'Validated' if validate_only else 'Created'} {len(config_data['schemes'])} color scheme(s)\n"
    )


@pytest.mark.parametrize("should_fail", [True, False])
def test_config_schema(monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture, tmp_path: Path, should_fail: bool):
    monkeypatch.setattr("sublime_lojoja_colors.PROJECT_DIR", tmp_path)
    context = does_not_raise()

    file = tmp_path / "config.schema.json"
    monkeypatch.setattr("sublime_lojoja_colors.CONFIG_SCHEMA_FILE", file)

    if should_fail:
        context = pytest.raises(OSError)
        mocker.patch("sublime_lojoja_colors.Path.write_text", side_effect=OSError)

    with context:
        config_schema()

    assert file.exists() is not should_fail


def test_construct_color_scheme():
    scheme = Scheme(name="x", author="x", palettes=["x"])
    template = SublimeColorSchemeTemplate(globals={"x": "ty"}, variables={"x": "tx"}, rules=[{"tx": "ty"}])
    palettes = {"x": Palette(globals={"x": "px", "y": "py"}, variables={"x": "px", "y": "py"})}
    constructed = construct_color_scheme(scheme, template, palettes)

    assert constructed.name == scheme.name
    assert constructed.author == scheme.author
    assert constructed.globals == template.globals | palettes["x"].globals
    assert constructed.variables == template.variables | palettes["x"].variables
    assert constructed.rules == template.rules


@pytest.mark.parametrize("should_fail", [True, False])
def test_save_color_scheme(monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture, tmp_path: Path, should_fail: bool):
    monkeypatch.setattr("sublime_lojoja_colors.PROJECT_DIR", tmp_path)
    context = does_not_raise()
    scheme = SublimeColorScheme(name="x", author="x", variables={"x": "y"}, globals={"x": "y"}, rules=[{"x": "y"}])
    file = tmp_path / f"{scheme.name}.sublime-color-scheme"

    if should_fail:
        context = pytest.raises(OSError)
        mocker.patch("sublime_lojoja_colors.Path.write_text", side_effect=OSError)

    with context:
        save_color_scheme(scheme)

    assert file.exists() is not should_fail


def test_validate(mocker: MockerFixture):
    mock_build = mocker.patch("sublime_lojoja_colors.build")
    validate()
    mock_build.assert_called_once_with(validate_only=True)
