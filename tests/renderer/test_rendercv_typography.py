import json

import pytest
import rendercv_fonts
import typst

from rendercv.renderer.pdf_png import get_package_path

ROLE_PROBES = """
#let probe(role) = context metadata((
  role: role, weight: text.weight, tracking: repr(text.tracking), kerning: text.kerning,
))
= Name #probe("name") *Strong #probe("name-strong")*
#headline([Headline #probe("headline") *Strong #probe("headline-strong")*])
#connections([Connections #probe("connections") *Strong #probe("connections-strong")*])
== Section #probe("section-titles") *Strong #probe("section-titles-strong")*
Body #probe("body") *Strong #probe("body-strong")*
*Outer #strong[Inner #probe("body-nested-strong")]*
"""


def typography_source(arguments: str, body: str) -> bytes:
    """Create a small document exercising the bundled Typst renderer.

    Args:
        arguments: Optional rendercv arguments to test.
        body: Typst content after applying the renderer.

    Returns:
        UTF-8 source for an offline Typst compilation.
    """
    return (
        '#import "@preview/rendercv:0.3.0": *\n'
        "#show: rendercv.with(\n"
        '  typography-font-family-body: "Source Sans 3",\n'
        '  typography-font-family-name: "Source Sans 3",\n'
        '  typography-font-family-headline: "Source Sans 3",\n'
        '  typography-font-family-connections: "Source Sans 3",\n'
        '  typography-font-family-section-titles: "Source Sans 3",\n'
        "  page-show-footer: false, page-show-top-note: false,\n"
        + arguments
        + "\n)\n"
        + body
    ).encode()


def role_properties(arguments: str) -> dict[str, dict[str, object]]:
    """Query effective weight and tracking in each typography role.

    Args:
        arguments: Optional rendercv arguments to test.

    Returns:
        Properties recorded within each role and its strong content.
    """
    compiler = typst.Compiler(
        typography_source(arguments, ROLE_PROBES),
        font_paths=typst.Fonts(
            include_system_fonts=False, font_paths=rendercv_fonts.paths_to_font_folders
        ),
        package_path=get_package_path(),
    )
    records = json.loads(compiler.query("metadata", field="value"))
    return {record["role"]: record for record in records if isinstance(record, dict)}


class TestRendercvFontControls:
    @pytest.mark.parametrize("legacy_bold", [False, True])
    def test_explicit_base_weight_wins_legacy_bold_for_every_role(
        self, legacy_bold: bool
    ):
        arguments = "\n".join(
            f"  typography-font-weight-{role}: 350,\n"
            f"  typography-bold-weight-{role}: 650,"
            for role in ("body", "name", "headline", "connections", "section-titles")
        )
        arguments += "\n" + "\n".join(
            f"  typography-bold-{role}: {str(legacy_bold).lower()},"
            for role in ("name", "headline", "connections", "section-titles")
        )

        properties = role_properties(arguments)

        for role in ("body", "name", "headline", "connections", "section-titles"):
            assert properties[role]["weight"] == 350
            assert properties[role + "-strong"]["weight"] == 650
        assert properties["body-nested-strong"]["weight"] == 650

    @pytest.mark.parametrize("legacy_bold", [False, True])
    def test_bold_selection_applies_to_legacy_bold_roles_when_base_is_omitted(
        self, legacy_bold: bool
    ):
        arguments = "\n".join(
            f"  typography-bold-weight-{role}: 650,"
            for role in ("body", "name", "headline", "connections", "section-titles")
        )
        arguments += "\n" + "\n".join(
            f"  typography-bold-{role}: {str(legacy_bold).lower()},"
            for role in ("name", "headline", "connections", "section-titles")
        )

        properties = role_properties(arguments)

        for role in ("name", "headline", "connections", "section-titles"):
            assert properties[role]["weight"] == (650 if legacy_bold else "regular")
            assert properties[role + "-strong"]["weight"] == 650
        assert properties["body"]["weight"] == "regular"
        assert properties["body-strong"]["weight"] == 650

    def test_body_controls_do_not_leak_into_other_roles(self):
        properties = role_properties(
            "  typography-font-weight-body: 350,\n"
            "  typography-bold-weight-body: 650,\n"
            "  typography-letter-spacing-body: 0.05em,\n"
        )

        assert properties["body"]["tracking"] == "0.05em"
        assert properties["body-strong"]["weight"] == 650
        for role in ("name", "headline", "connections", "section-titles"):
            assert properties[role]["weight"] == "regular"
            assert properties[role + "-strong"]["weight"] == "bold"
            assert properties[role]["tracking"] == "0pt"
            assert properties[role + "-strong"]["tracking"] == "0pt"
        assert all(record["kerning"] is True for record in properties.values())

    def test_independent_tracking_overrides_keep_kerning(self):
        roles = ("body", "name", "headline", "connections", "section-titles")
        properties = role_properties(
            "\n".join(
                f"  typography-letter-spacing-{role}: 0.0{number}em,"
                for number, role in enumerate(roles, start=1)
            )
        )

        for number, role in enumerate(roles, start=1):
            assert properties[role]["tracking"] == f"0.0{number}em"
            assert properties[role]["kerning"] is True


class TestRendercvSectionTitleGap:
    @pytest.mark.parametrize(
        ("style", "changes_output"),
        [
            ("centered_with_partial_line", True),
            ("centered_with_centered_partial_line", True),
            ("with_full_line", False),
        ],
    )
    def test_gap_changes_only_centred_partial_lines(
        self, style: str, changes_output: bool
    ):
        images: list[bytes | list[bytes]] = []
        for gap in (None, "0.3em", "1em"):
            arguments = f'  section-titles-type: "{style}",\n'
            if gap is not None:
                arguments += f"  section-titles-space-between-text-and-line: {gap},\n"
            compiler = typst.Compiler(
                typography_source(arguments, "= Name\n== Section Title\nBody"),
                font_paths=typst.Fonts(
                    include_system_fonts=False,
                    font_paths=rendercv_fonts.paths_to_font_folders,
                ),
                package_path=get_package_path(),
            )
            image = compiler.compile(format="png")
            assert image is not None
            images.append(image)

        assert images[0] == images[1]
        assert (images[0] != images[2]) is changes_output
