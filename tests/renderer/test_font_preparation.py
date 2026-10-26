import hashlib
import pathlib
import re
from typing import cast

import pytest
import typst
from fontTools.designspaceLib import (
    AxisDescriptor,
    DesignSpaceDocument,
    SourceDescriptor,
)
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.varLib import build

from rendercv.renderer.font_preparation import FontWeightTable, prepare_font_directory
from rendercv.renderer.pdf_png import generate_pdf, generate_png
from rendercv.renderer.typst import generate_typst
from rendercv.schema.models.design.font_settings import FontSettings
from rendercv.schema.models.rendercv_model import RenderCVModel
from rendercv.schema.models.validation_context import ValidationContext


def build_variable_font(
    folder: pathlib.Path, maximum_weight: int = 900, width_axis: bool = False
) -> pathlib.Path:
    """Build a tiny, real variable font with weight and italic outline changes.

    Args:
        folder: Temporary directory for masters and the resulting font.
        maximum_weight: Maximum coordinate of the test font's weight axis.
        width_axis: Include an additional width axis with a narrow default.

    Returns:
        Path to an offline test font with wght and ital axes.
    """
    designspace = DesignSpaceDocument()
    axes = [
        ("Weight", "wght", 100, 400, maximum_weight),
        ("Italic", "ital", 0, 0, 1),
    ]
    if width_axis:
        axes.append(("Width", "wdth", 75, 75, 125))
    for name, tag, minimum, default, maximum in axes:
        axis = AxisDescriptor()
        axis.name, axis.tag = name, tag
        axis.minimum, axis.default, axis.maximum = minimum, default, maximum
        designspace.addAxis(axis)

    for weight in (100, 400, maximum_weight):
        for italic in (0, 1):
            path = folder / f"master-{weight}-{italic}.ttf"
            builder = FontBuilder(1000, isTTF=True)
            builder.setupGlyphOrder([".notdef", "M"])
            builder.setupCharacterMap({ord("M"): "M"})
            glyphs = {}
            for glyph_name in (".notdef", "M"):
                pen = TTGlyphPen(None)
                stem = 30 + weight * 0.25
                pen.moveTo((50, 0))
                pen.lineTo((50 + stem, 0))
                pen.lineTo((50 + stem + italic * 100, 700))
                pen.lineTo((50 + italic * 100, 700))
                pen.closePath()
                glyphs[glyph_name] = pen.glyph()
            builder.setupGlyf(glyphs)
            builder.setupHorizontalMetrics(dict.fromkeys(glyphs, (600, 50)))
            builder.setupHorizontalHeader(ascent=800, descent=-200)
            builder.setupNameTable(
                {
                    "familyName": "RenderCV Test Variable",
                    "styleName": "Regular" if not italic else "Italic",
                    "psName": f"RenderCVTestMaster{weight}I{italic}",
                    "uniqueFontIdentifier": f"RenderCVTestMaster{weight}I{italic}",
                }
            )
            builder.setupOS2(
                sTypoAscender=800,
                sTypoDescender=-200,
                usWinAscent=800,
                usWinDescent=200,
                usWeightClass=weight,
            )
            builder.setupPost()
            builder.setupMaxp()
            builder.save(path)
            source = SourceDescriptor()
            source.path = str(path)
            source.name = path.stem
            source.familyName = "RenderCV Test Variable"
            source.styleName = "Regular" if not italic else "Italic"
            source.designLocation = {"Weight": weight, "Italic": italic}
            if width_axis:
                source.designLocation["Width"] = 75
            source.copyInfo = source.copyLib = weight == 400 and italic == 0
            designspace.addSource(source)
    variable, _, _ = build(designspace)
    output = folder / "variable.ttf"
    variable.save(output)
    variable.close()
    return output


@pytest.fixture
def variable_model(tmp_path: pathlib.Path) -> tuple[RenderCVModel, pathlib.Path]:
    font_folder = tmp_path / "fonts"
    font_folder.mkdir()
    source_font = build_variable_font(font_folder)
    # Keep masters out of font discovery: the test must exercise one variable file.
    for master in font_folder.glob("master-*.ttf"):
        master.unlink()
    model = RenderCVModel.model_validate(
        {
            "cv": {"name": "John Doe", "sections": {"Test": ["MMM **MMM** ***MMM***"]}},
            "design": {
                "theme": "classic",
                "typography": {
                    "font_family": {
                        "body": {
                            "family": "RenderCV Test Variable",
                            "weight": 350,
                            "bold_weight": 650,
                            "letter_spacing": 1.05,
                        }
                    }
                },
            },
            "settings": {"current_date": "2025-11-30"},
        },
        context={"context": ValidationContext(input_file_path=tmp_path / "cv.yaml")},
    )
    return model, source_font


class TestPrepareFontDirectory:
    @pytest.mark.parametrize("font", ["Raleway", {"family": "Raleway", "weight": 400}])
    def test_static_and_legacy_selections_need_no_preparation(
        self, font: str | dict[str, object]
    ):
        model = RenderCVModel.model_validate(
            {
                "design": {
                    "theme": "classic",
                    "typography": {"font_family": {"body": font}},
                }
            }
        )

        assert prepare_font_directory(model) is None

    def test_renders_different_exact_weights_without_mutating_source(
        self, variable_model: tuple[RenderCVModel, pathlib.Path]
    ):
        model, source = variable_model
        original_digest = hashlib.sha256(source.read_bytes()).digest()
        folder = prepare_font_directory(model)
        assert folder is not None
        assert prepare_font_directory(model) == folder
        faces = [
            face
            for face in typst.Fonts(
                include_system_fonts=False,
                include_embedded_fonts=False,
                font_paths=[folder],
            ).fonts()
            if face.family == "RenderCV Test Variable"
        ]
        assert {(350, "normal"), (350, "italic"), (650, "normal"), (650, "italic")} <= {
            (face.weight, face.style) for face in faces
        }
        for face in faces:
            assert face.path is not None
            with TTFont(face.path) as font:
                assert "fvar" not in font
        images: list[bytes | list[bytes]] = []
        for weight, style in ((350, "normal"), (650, "normal"), (350, "italic")):
            compiler = typst.Compiler(
                (
                    '#set text(font: "RenderCV Test Variable", '
                    f'weight: {weight}, style: "{style}")\nMMM'
                ).encode(),
                font_paths=typst.Fonts(include_system_fonts=False, font_paths=[folder]),
            )
            image, warnings = compiler.compile_with_warnings(format="png")
            assert not warnings
            assert image is not None
            images.append(image)
        assert images[0] != images[1]
        assert images[0] != images[2]
        assert hashlib.sha256(source.read_bytes()).digest() == original_digest

    def test_preserves_source_width_matching_category(
        self, variable_model: tuple[RenderCVModel, pathlib.Path]
    ):
        model, source = variable_model
        build_variable_font(source.parent, width_axis=True)
        for master in source.parent.glob("master-*.ttf"):
            master.unlink()
        with TTFont(source) as font:
            cast(FontWeightTable, font["OS/2"]).usWidthClass = 5
            font.save(source)
        folder = prepare_font_directory(model)
        assert folder is not None
        faces = typst.Fonts(
            include_system_fonts=False,
            include_embedded_fonts=False,
            font_paths=[folder],
        ).fonts()
        assert all(
            face.stretch == 1.0
            for face in faces
            if face.family == "RenderCV Test Variable"
        )

    def test_native_strong_uses_available_axis_endpoint(
        self, variable_model: tuple[RenderCVModel, pathlib.Path]
    ):
        model, source = variable_model
        build_variable_font(source.parent, maximum_weight=650)
        for master in source.parent.glob("master-*.ttf"):
            master.unlink()
        families = model.design.typography.font_family
        assert not isinstance(families, str)
        families.body = FontSettings.model_validate(
            {"family": "RenderCV Test Variable", "weight": 600},
            context={
                "context": ValidationContext(input_file_path=model._input_file_path)
            },
        )
        folder = prepare_font_directory(model)
        assert folder is not None
        compiler = typst.Compiler(
            b'#set text(font: "RenderCV Test Variable", weight: 600)\n*MMM*',
            font_paths=typst.Fonts(include_system_fonts=False, font_paths=[folder]),
        )
        pdf = compiler.compile()
        assert isinstance(pdf, bytes)
        font_names = re.findall(rb"/BaseFont /([^ /\r\n]+)", pdf)
        assert any(b"W650Normal" in name for name in font_names)

    @pytest.mark.parametrize("explicit_bold", [False, True])
    def test_pdf_and_png_use_prepared_weights_and_real_italic(
        self,
        variable_model: tuple[RenderCVModel, pathlib.Path],
        tmp_path: pathlib.Path,
        explicit_bold: bool,
    ):
        model, _ = variable_model
        if not explicit_bold:
            families = model.design.typography.font_family
            assert not isinstance(families, str)
            families.body = FontSettings.model_validate(
                {"family": "RenderCV Test Variable", "weight": 350},
                context={
                    "context": ValidationContext(input_file_path=model._input_file_path)
                },
            )
        model.settings.render_command.typst_path = tmp_path / "cv.typ"
        model.settings.render_command.pdf_path = tmp_path / "cv.pdf"
        model.settings.render_command.png_path = tmp_path / "cv.png"
        source = generate_typst(model)
        assert source is not None
        assert "typography-font-weight-body: 350," in source.read_text(encoding="utf-8")
        pdf = generate_pdf(model, source)
        pngs = generate_png(model, source)
        assert pdf is not None
        font_names = re.findall(rb"/BaseFont /([^ /\r\n]+)", pdf.read_bytes())
        assert any(b"W350Normal" in name for name in font_names)
        assert any(b"W650Normal" in name for name in font_names)
        assert any(b"W650Italic" in name for name in font_names)
        assert pngs is not None
        assert all(path.is_file() for path in pngs)
