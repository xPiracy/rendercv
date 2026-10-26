import re

import pydantic
import pytest

from rendercv.schema.models.design.font_settings import (
    FontSettings,
    FontWeight,
    FontWeightName,
    font_weight_aliases,
)
from rendercv.schema.models.rendercv_model import RenderCVModel
from rendercv.schema.models.validation_context import ValidationContext


class TestFontSettings:
    def test_omitted_controls_preserve_font_behaviour(self):
        settings = FontSettings(family="Source Sans 3")

        assert str(settings) == "Source Sans 3"
        assert settings.resolved_weight is None
        assert settings.resolved_bold_weight is None
        assert settings.resolved_tracking is None

    def test_rejects_unavailable_family(self):
        with pytest.raises(pydantic.ValidationError, match="is not available"):
            FontSettings(family="RenderCV Family That Does Not Exist")

    @pytest.mark.parametrize("family", ["Source Sans 3", "source sans 3"])
    def test_accepts_metadata_family_case_insensitively(self, family):
        assert FontSettings(family=family, weight=700).resolved_weight == 700

    @pytest.mark.parametrize("field", ["weight", "bold_weight"])
    @pytest.mark.parametrize("value", [True, False, 400.0, "400", 99, 901])
    def test_rejects_invalid_numeric_weights(self, field, value):
        with pytest.raises(pydantic.ValidationError):
            FontSettings.model_validate({"family": "Source Sans 3", field: value})

    @pytest.mark.parametrize(
        "selectors",
        [
            {"weight": 400, "weight_name": "regular"},
            {"bold_weight": 700, "bold_weight_name": "bold"},
        ],
    )
    def test_rejects_conflicting_selectors(self, selectors):
        with pytest.raises(pydantic.ValidationError, match="Use either"):
            FontSettings.model_validate({"family": "Source Sans 3", **selectors})

    def test_accepts_null_alternative_selectors(self):
        settings = FontSettings(
            family="Source Sans 3",
            weight=400,
            weight_name=None,
            bold_weight=None,
            bold_weight_name="bold",
        )
        assert settings.resolved_weight == 400
        assert settings.resolved_bold_weight == 700

    @pytest.mark.parametrize("selectors", [{"weight": 350}, {"weight_name": "thin"}])
    def test_rejects_unavailable_static_weight(self, selectors):
        with pytest.raises(pydantic.ValidationError, match="does not provide"):
            FontSettings.model_validate({"family": "Source Sans 3", **selectors})

    @pytest.mark.parametrize(
        ("spacing", "expected"),
        [
            (None, None),
            ("default", None),
            (1, None),
            (1.0, None),
            (1.05, "0.05em"),
            (0.95, "-0.05em"),
            (2, "1.0em"),
            ("0.03em", "0.03em"),
            ("-0.01em", "-0.01em"),
            ("0pt", "0pt"),
        ],
    )
    def test_resolves_letter_spacing(self, spacing, expected):
        assert (
            FontSettings(
                family="Source Sans 3", letter_spacing=spacing
            ).resolved_tracking
            == expected
        )

    @pytest.mark.parametrize(
        "spacing",
        [True, False, 0, -0.5, float("inf"), float("nan"), "1.05", "normal", "0.3px"],
    )
    def test_rejects_invalid_letter_spacing(self, spacing):
        with pytest.raises(pydantic.ValidationError):
            FontSettings(family="Source Sans 3", letter_spacing=spacing)

    def test_rejects_unknown_control(self):
        with pytest.raises(pydantic.ValidationError, match="extra_forbidden"):
            FontSettings.model_validate(
                {"family": "Source Sans 3", "unknown_control": 400}
            )

    def test_resolves_actual_named_weight_from_local_metadata(
        self, font_settings_folder
    ):
        settings = FontSettings.model_validate(
            {
                "family": "RenderCV Metadata Test",
                "weight_name": "Thin",
                "bold_weight_name": "Semi Bold",
            },
            context={
                "context": ValidationContext(
                    input_file_path=font_settings_folder.parent / "cv.yaml"
                )
            },
        )
        assert settings.resolved_weight == 280
        assert settings.resolved_bold_weight == 600

    def test_preserves_input_path_through_design_validation(self, font_settings_folder):
        model = RenderCVModel.model_validate(
            {
                "design": {
                    "theme": "classic",
                    "typography": {
                        "font_family": {
                            "body": {"family": "RenderCV Metadata Test", "weight": 280}
                        }
                    },
                }
            },
            context={
                "context": ValidationContext(
                    input_file_path=font_settings_folder.parent / "cv.yaml"
                )
            },
        )
        assert model.design.typography.font_family.body.resolved_weight == 280

    def test_preserves_input_path_for_custom_theme(self, font_settings_folder):
        theme_folder = font_settings_folder.parent / "metadatatheme"
        theme_folder.mkdir()
        (theme_folder / "EducationEntry.j2.typ").touch()
        (theme_folder / "__init__.py").write_text(
            "from typing import Literal\n"
            "from rendercv.schema.models.design.classic_theme import ClassicTheme\n"
            "class MetadatathemeTheme(ClassicTheme):\n"
            "    theme: Literal['metadatatheme'] = 'metadatatheme'\n",
            encoding="utf-8",
        )
        model = RenderCVModel.model_validate(
            {
                "design": {
                    "theme": "metadatatheme",
                    "typography": {
                        "font_family": {
                            "body": {
                                "family": "RenderCV Metadata Test",
                                "weight_name": "thin",
                            }
                        }
                    },
                }
            },
            context={
                "context": ValidationContext(
                    input_file_path=font_settings_folder.parent / "cv.yaml"
                )
            },
        )
        assert model.design.typography.font_family.body.resolved_weight == 280

    @pytest.mark.parametrize("weight", [100, 350, 650, 900])
    def test_accepts_numeric_weight_within_variable_axis(
        self, font_settings_folder, weight
    ):
        settings = FontSettings.model_validate(
            {"family": "RenderCV Variable Test", "weight": weight},
            context={
                "context": ValidationContext(
                    input_file_path=font_settings_folder.parent / "cv.yaml"
                )
            },
        )
        assert settings.resolved_weight == weight

    def test_does_not_invent_named_variable_instances(self, font_settings_folder):
        with pytest.raises(pydantic.ValidationError, match="named 'light'"):
            FontSettings.model_validate(
                {"family": "RenderCV Variable Test", "weight_name": "light"},
                context={
                    "context": ValidationContext(
                        input_file_path=font_settings_folder.parent / "cv.yaml"
                    )
                },
            )

    def test_schema_accepts_custom_families_and_weight_aliases(self):
        schema = FontSettings.model_json_schema()
        assert schema["properties"]["family"]["type"] == "string"
        assert "enum" not in schema["properties"]["family"]
        pattern = schema["$defs"]["FontWeightName"]["pattern"]
        for name in font_weight_aliases:
            assert re.fullmatch(pattern, name.upper())

    @pytest.mark.parametrize(
        ("spacing", "valid"),
        [
            ("0pt", True),
            ("0.03em", True),
            ("-0.01em", True),
            ("2cm", True),
            ("0.5in", True),
            ("1mm", True),
            ("narrow", False),
            ("1.05", False),
            ("0.3px", False),
            ("0.3em extra", False),
            ("0.3em\n", False),
            ("0.3em\njunk", False),
        ],
    )
    def test_schema_restricts_letter_spacing_dimensions(self, spacing, valid):
        schema = FontSettings.model_json_schema()
        dimension = schema["$defs"]["SpacingDimension"]
        assert dimension["type"] == "string"
        assert bool(re.search(dimension["pattern"], spacing)) is valid

    def test_schema_preserves_default_factor_and_null_letter_spacing(self):
        schema = FontSettings.model_json_schema()
        assert schema["$defs"]["LetterSpacing"]["anyOf"] == [
            {"const": "default", "type": "string"},
            {"exclusiveMinimum": 0, "type": "number"},
            {"$ref": "#/$defs/SpacingDimension"},
        ]
        assert schema["properties"]["letter_spacing"]["anyOf"] == [
            {"$ref": "#/$defs/LetterSpacing"},
            {"type": "null"},
        ]


class TestFontWeightName:
    @pytest.mark.parametrize("name", font_weight_aliases)
    def test_normalizes_human_readable_names(self, name):
        adapter = pydantic.TypeAdapter(FontWeightName)
        assert adapter.validate_python(name.upper()) == name.replace(" ", "").replace(
            "-", ""
        )

    @pytest.mark.parametrize("name", ["normal", "th in", "b-old", 400, True])
    def test_rejects_unknown_names(self, name):
        with pytest.raises(pydantic.ValidationError):
            pydantic.TypeAdapter(FontWeightName).validate_python(name)


@pytest.mark.parametrize("weight", [100, 280, 350, 650, 900])
def test_font_weight_accepts_any_integer_in_range(weight):
    assert pydantic.TypeAdapter(FontWeight).validate_python(weight) == weight
