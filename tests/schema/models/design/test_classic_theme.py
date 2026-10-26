import re

import pydantic
import pytest

from rendercv.schema.models.design.classic_theme import (
    FontFamily,
    SectionTitles,
    Typography,
)
from rendercv.schema.models.design.font_settings import FontSettings


class TestTypography:
    def test_legacy_families_do_not_scan_fonts(self, monkeypatch):
        def unexpected_scan(_folder):
            pytest.fail("Legacy font families must not trigger font discovery")

        monkeypatch.setattr(
            "rendercv.schema.models.design.font_settings.get_font_faces",
            unexpected_scan,
        )
        typography = Typography(font_family="User Font")
        assert isinstance(typography.font_family, FontFamily)
        assert typography.font_family.body == "User Font"

    def test_accepts_font_family_as_string(self):
        typography = Typography(font_family="Arial")

        assert isinstance(typography.font_family, FontFamily)
        assert typography.font_family.body == "Arial"
        assert typography.font_family.name == "Arial"
        assert typography.font_family.headline == "Arial"
        assert typography.font_family.connections == "Arial"
        assert typography.font_family.section_titles == "Arial"

    def test_accepts_font_family_as_dict(self):
        typography = Typography(
            font_family={
                "body": "Arial",
                "name": "Georgia",
                "headline": "Helvetica",
                "connections": "Verdana",
                "section_titles": "Tahoma",
            }
        )

        assert isinstance(typography.font_family, FontFamily)
        assert typography.font_family.body == "Arial"
        assert typography.font_family.name == "Georgia"
        assert typography.font_family.headline == "Helvetica"
        assert typography.font_family.connections == "Verdana"
        assert typography.font_family.section_titles == "Tahoma"

    def test_accepts_mixed_family_strings_and_settings(self):
        typography = Typography(
            font_family={
                "body": {
                    "family": "Source Sans 3",
                    "weight": 400,
                    "bold_weight_name": "bold",
                    "letter_spacing": 1.05,
                },
                "name": "Source Sans 3",
            }
        )
        assert isinstance(typography.font_family, FontFamily)
        assert isinstance(typography.font_family.body, FontSettings)
        assert typography.font_family.body.resolved_weight == 400
        assert typography.font_family.body.resolved_bold_weight == 700
        assert typography.font_family.body.resolved_tracking == "0.05em"
        assert typography.font_family.name == "Source Sans 3"


class TestSectionTitles:
    def test_omitted_text_to_line_gap_preserves_spacing(self):
        assert SectionTitles().space_between_text_and_line is None

    @pytest.mark.parametrize("gap", [None, "0pt", "0.8em", "0.2cm", "-0.01em"])
    def test_accepts_optional_text_to_line_gap(self, gap):
        assert (
            SectionTitles(space_between_text_and_line=gap).space_between_text_and_line
            == gap
        )

    @pytest.mark.parametrize("gap", [0, True, "default", "0.5px"])
    def test_rejects_invalid_text_to_line_gap(self, gap):
        with pytest.raises(pydantic.ValidationError):
            SectionTitles(space_between_text_and_line=gap)

    @pytest.mark.parametrize(
        ("gap", "valid"),
        [
            ("0pt", True),
            ("0.8em", True),
            ("-0.01em", True),
            ("0.2cm", True),
            ("0.5in", True),
            ("1mm", True),
            ("narrow", False),
            ("default", False),
            ("0.5px", False),
            ("0.3em\n", False),
            ("0.3em\njunk", False),
        ],
    )
    def test_schema_restricts_text_to_line_gap_dimensions(self, gap, valid):
        schema = SectionTitles.model_json_schema()
        dimension = schema["$defs"]["SpacingDimension"]
        assert dimension["type"] == "string"
        assert bool(re.search(dimension["pattern"], gap)) is valid

    def test_schema_preserves_optional_text_to_line_gap(self):
        schema = SectionTitles.model_json_schema()
        gap = schema["properties"]["space_between_text_and_line"]
        assert gap["anyOf"] == [
            {"$ref": "#/$defs/SpacingDimension"},
            {"type": "null"},
        ]
        assert gap["default"] is None
