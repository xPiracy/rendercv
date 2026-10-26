import pytest

from rendercv.renderer.templater.templater import render_full_template
from rendercv.renderer.typst import generate_typst
from rendercv.schema.models.design.built_in_design import available_themes
from rendercv.schema.models.rendercv_model import RenderCVModel


@pytest.mark.parametrize("theme", available_themes)
@pytest.mark.parametrize("cv_variant", ["minimal", "full"])
def test_generate_typst(
    compare_file_with_reference,
    theme: str,
    cv_variant: str,
    request: pytest.FixtureRequest,
):
    base_model = request.getfixturevalue(f"{cv_variant}_rendercv_model")

    model = RenderCVModel(
        cv=base_model.cv,
        design={"theme": theme},
        locale=base_model.locale,
        settings=base_model.settings,
    )

    def generate_file(output_path):
        model.settings.render_command.typst_path = output_path
        generate_typst(model)

    reference_filename = f"{theme}_{cv_variant}.typ"
    assert compare_file_with_reference(generate_file, reference_filename)


class TestGenerateTypstFontSettings:
    @pytest.mark.parametrize(
        "role", ["body", "name", "headline", "connections", "section_titles"]
    )
    @pytest.mark.parametrize("named", [False, True])
    def test_emits_requested_controls_for_each_role(self, role: str, named: bool):
        selectors = (
            {"weight_name": "regular", "bold_weight_name": "bold"}
            if named
            else {"weight": 400, "bold_weight": 700}
        )
        model = RenderCVModel.model_validate(
            {
                "cv": {"name": "John Doe"},
                "design": {
                    "theme": "classic",
                    "typography": {
                        "font_family": {
                            role: {
                                "family": "Raleway",
                                **selectors,
                                "letter_spacing": 1.05,
                            }
                        }
                    },
                },
            }
        )

        result = render_full_template(model, "typst")
        typst_role = role.replace("_", "-")
        assert f'typography-font-family-{typst_role}: "Raleway",' in result
        assert f"typography-font-weight-{typst_role}: 400," in result
        assert f"typography-bold-weight-{typst_role}: 700," in result
        assert f"typography-letter-spacing-{typst_role}: 0.05em," in result

    @pytest.mark.parametrize("spacing", [None, "default", 1])
    def test_default_object_matches_legacy_family_string(
        self, spacing: str | int | None
    ):
        model = RenderCVModel.model_validate(
            {"design": {"theme": "classic", "typography": {"font_family": "Raleway"}}}
        )
        expected = render_full_template(model, "typst")
        model = RenderCVModel.model_validate(
            {
                "design": {
                    "theme": "classic",
                    "typography": {
                        "font_family": {
                            role: {"family": "Raleway", "letter_spacing": spacing}
                            for role in (
                                "body",
                                "name",
                                "headline",
                                "connections",
                                "section_titles",
                            )
                        }
                    },
                }
            }
        )

        assert render_full_template(model, "typst") == expected

    def test_emits_optional_section_title_line_gap(self):
        model = RenderCVModel.model_validate(
            {
                "design": {
                    "theme": "classic",
                    "section_titles": {
                        "type": "centered_with_centered_partial_line",
                        "space_between_text_and_line": "0.8em",
                    },
                }
            }
        )

        assert "section-titles-space-between-text-and-line: 0.8em," in (
            render_full_template(model, "typst")
        )
