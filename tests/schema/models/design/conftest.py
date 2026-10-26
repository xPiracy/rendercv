import pathlib
from typing import Protocol, cast

import pytest
import rendercv_fonts
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._f_v_a_r import Axis, NamedInstance, table__f_v_a_r


class WeightTable(Protocol):
    usWeightClass: int
    usWidthClass: int


@pytest.fixture
def font_settings_folder(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create portable local fonts with actual, controlled metadata."""
    folder = tmp_path / "fonts"
    folder.mkdir()
    source = next(
        path
        for path in rendercv_fonts.paths_to_font_files
        if path.name == "SourceSans3-Regular.ttf"
    )
    weights = {
        "Thin": 280,
        "Extra Light": 200,
        "Light": 300,
        "Regular": 400,
        "Medium": 500,
        "Semi Bold": 600,
        "Bold": 700,
        "Extra Bold": 800,
        "Black": 900,
    }
    for name, weight in weights.items():
        with TTFont(source) as font:
            font["name"].names = [
                record
                for record in font["name"].names
                if record.nameID not in {1, 2, 3, 4, 6, 16, 17}
            ]
            for name_id, text in {
                1: "RenderCV Metadata Test",
                2: name,
                3: f"RenderCVMetadataTest-{weight}",
                4: f"RenderCV Metadata Test {name}",
                6: f"RenderCVMetadataTest-{weight}",
                16: "RenderCV Metadata Test",
                17: name,
            }.items():
                font["name"].setName(text, name_id, 3, 1, 0x409)
            cast(WeightTable, font["OS/2"]).usWeightClass = weight
            font.save(folder / f"Test-{weight}.ttf")

    with TTFont(folder / "Test-400.ttf") as font:
        for name_id in (1, 16):
            font["name"].setName("RenderCV Variable Test", name_id, 3, 1, 0x409)
        variable = table__f_v_a_r()
        axis = Axis()
        axis.axisTag = "wght"
        axis.minValue = 100
        axis.defaultValue = 400
        axis.maxValue = 900
        axis.flags = 0
        axis.axisNameID = font["name"].addName("Weight")
        variable.axes = [axis]
        variable.instances = []
        for name, weight in (("Thin", 280), ("Regular", 400), ("Black", 900)):
            instance = NamedInstance()
            instance.subfamilyNameID = font["name"].addName(name)
            instance.flags = 0
            instance.coordinates = {"wght": weight}
            variable.instances.append(instance)
        font["fvar"] = variable
        font.save(folder / "Variable.ttf")

    return folder


@pytest.fixture
def font_variant_folder(font_settings_folder: pathlib.Path) -> pathlib.Path:
    """Create one family whose alternate styles have otherwise missing weights."""
    folder = font_settings_folder / "variants"
    folder.mkdir()
    for weight, subfamily, width in (
        (400, "Regular", 5),
        (280, "Thin Italic", 5),
        (300, "Light Condensed", 3),
    ):
        with TTFont(font_settings_folder / f"Test-{weight}.ttf") as font:
            for name_id, text in {
                1: "RenderCV Variant Test",
                2: subfamily,
                4: f"RenderCV Variant Test {subfamily}",
                6: f"RenderCVVariantTest-{weight}",
                16: "RenderCV Variant Test",
                17: subfamily,
            }.items():
                font["name"].setName(text, name_id, 3, 1, 0x409)
            cast(WeightTable, font["OS/2"]).usWidthClass = width
            font.save(folder / f"Variant-{weight}.ttf")
    return folder
