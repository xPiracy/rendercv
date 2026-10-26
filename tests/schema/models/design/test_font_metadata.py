import pathlib

import pytest
import typst
from fontTools.ttLib import TTCollection, TTFont
from fontTools.ttLib.tables._f_v_a_r import Axis

from rendercv.schema.models.design.font_metadata import (
    get_face_metadata,
    get_font_faces,
    normalize_subfamily_name,
    read_font_metadata,
    resolve_font_weight,
)
from rendercv.schema.models.design.font_settings import font_weight_names


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Thin", "thin"),
        ("Extra Light Italic", "extralight"),
        ("SemiBold Oblique", "semibold"),
        ("Italic", "regular"),
        ("Book", "regular"),
        ("Roman", "regular"),
    ],
)
def test_normalize_subfamily_name(name, expected):
    assert normalize_subfamily_name(name) == expected


class TestGetFontFaces:
    def test_uses_local_metadata_and_caches_unchanged_discovery(
        self, font_settings_folder
    ):
        faces = get_font_faces(font_settings_folder)
        assert any(
            face.family == "RenderCV Metadata Test" and face.weight == 280
            for face in faces
        )
        assert get_font_faces(font_settings_folder) is faces

    def test_refreshes_discovery_when_fonts_are_added(self, font_settings_folder):
        faces = get_font_faces(font_settings_folder)
        with TTFont(font_settings_folder / "Test-400.ttf") as font:
            for name_id in (1, 16):
                font["name"].setName("RenderCV New Family", name_id, 3, 1, 0x409)
            font.save(font_settings_folder / "New.ttf")
        refreshed = get_font_faces(font_settings_folder)
        assert refreshed is not faces
        assert any(face.family == "RenderCV New Family" for face in refreshed)


class TestReadFontMetadata:
    def test_reads_nonstandard_weight_subfamily(self, font_settings_folder):
        face = next(
            face
            for face in get_font_faces(font_settings_folder)
            if face.family == "RenderCV Metadata Test" and face.weight == 280
        )
        metadata = get_face_metadata(face)
        assert metadata.weight == 280
        assert metadata.names == ("thin",)
        assert metadata.weight_range is None

    def test_reads_variable_axis_and_instances(self, font_settings_folder):
        face = next(
            face
            for face in get_font_faces(font_settings_folder)
            if face.family == "RenderCV Variable Test"
        )
        metadata = get_face_metadata(face)
        assert metadata.weight_range == (100, 900)
        assert ("thin", 280) in metadata.named_weights

    def test_uses_correct_face_index_for_collection(self, font_settings_folder):
        collection_path = font_settings_folder / "Collection.ttc"
        with (
            TTFont(font_settings_folder / "Test-280.ttf") as thin,
            TTFont(font_settings_folder / "Test-700.ttf") as bold,
        ):
            collection = TTCollection()
            collection.fonts = [thin, bold]
            collection.save(collection_path)
        stat = collection_path.stat()
        metadata = read_font_metadata(
            collection_path, 1, 700, stat.st_mtime_ns, stat.st_size
        )
        assert metadata.names == ("bold",)
        assert metadata.weight == 700

    def test_reports_unreadable_metadata(self, tmp_path: pathlib.Path):
        path = tmp_path / "Invalid.ttf"
        path.write_bytes(b"not a font")
        stat = path.stat()
        with pytest.raises(ValueError, match="Cannot read font weight metadata"):
            read_font_metadata(path, 0, 400, stat.st_mtime_ns, stat.st_size)

    def test_supports_typst_embedded_faces(self):
        face = next(
            face
            for face in typst.Fonts(include_system_fonts=False).fonts()
            if face.path is None
        )
        assert get_face_metadata(face).weight == face.weight

    @pytest.mark.parametrize(
        ("style", "style_axes", "upright"),
        [
            ("italic", (("ital", 0, 1, 1),), True),
            ("italic", (("ital", 0.2, 1, 1),), False),
            ("oblique", (("slnt", -12, -12, 0),), True),
            ("oblique", (("slnt", -12, -12, -2),), False),
            ("italic", (("ital", 0, 1, 1), ("slnt", -12, -12, -2)), False),
        ],
    )
    def test_detects_real_upright_axis_coordinates(
        self, font_settings_folder, style, style_axes, upright
    ):
        path = font_settings_folder / "Variable.ttf"
        with TTFont(path) as font:
            for axis_tag, minimum, default, maximum in style_axes:
                axis = Axis()
                axis.axisTag = axis_tag
                axis.minValue = minimum
                axis.defaultValue = default
                axis.maxValue = maximum
                axis.flags = 0
                axis.axisNameID = font["name"].addName("Style")
                font["fvar"].axes.append(axis)
                for instance in font["fvar"].instances:
                    instance.coordinates[axis_tag] = default
            font.save(path)
        stat = path.stat()
        metadata = read_font_metadata(
            path, 0, 400, stat.st_mtime_ns, stat.st_size, style=style
        )
        assert metadata.upright_instance is upright


class TestResolveFontWeight:
    def test_omitted_selectors_do_not_read_metadata(self):
        assert resolve_font_weight("Unused", (), None, None, font_weight_names) is None

    def test_resolves_named_variable_coordinate(self, font_settings_folder):
        faces = tuple(
            face
            for face in get_font_faces(font_settings_folder)
            if face.family == "RenderCV Variable Test"
        )
        assert (
            resolve_font_weight(
                "RenderCV Variable Test", faces, None, "thin", font_weight_names
            )
            == 280
        )

    def test_rejects_coordinate_outside_variable_axis(self, font_settings_folder):
        faces = tuple(
            face
            for face in get_font_faces(font_settings_folder)
            if face.family == "RenderCV Variable Test"
        )
        with pytest.raises(ValueError, match="does not provide weight 950"):
            resolve_font_weight(
                "RenderCV Variable Test", faces, 950, None, font_weight_names
            )

    @pytest.mark.parametrize(("name", "weight"), [("thin", 50), ("black", 1000)])
    def test_rejects_named_variable_weight_outside_typst_range(
        self, font_settings_folder, name, weight
    ):
        path = font_settings_folder / "Variable.ttf"
        with TTFont(path) as font:
            font["fvar"].axes[0].minValue = 1
            font["fvar"].axes[0].maxValue = 1000
            for instance in font["fvar"].instances:
                instance_name = font["name"].getDebugName(instance.subfamilyNameID)
                if instance_name and instance_name.lower() == name:
                    instance.coordinates["wght"] = weight
            font.save(path)
        faces = tuple(
            face
            for face in get_font_faces(font_settings_folder)
            if face.family == "RenderCV Variable Test"
        )
        with pytest.raises(ValueError, match="outside Typst's supported range"):
            resolve_font_weight(
                "RenderCV Variable Test", faces, None, name, font_weight_names
            )

    @pytest.mark.parametrize(
        ("weight", "name"), [(280, None), (None, "thin"), (300, None), (None, "light")]
    )
    def test_rejects_weights_in_less_suitable_style_or_stretch(
        self, font_variant_folder, weight, name
    ):
        faces = tuple(
            face
            for face in get_font_faces(font_variant_folder)
            if face.family == "RenderCV Variant Test"
        )
        with pytest.raises(ValueError, match="does not provide"):
            resolve_font_weight(
                "RenderCV Variant Test", faces, weight, name, font_weight_names
            )

    def test_preserves_native_style_fallback_without_upright_faces(
        self, font_variant_folder
    ):
        faces = tuple(
            face
            for face in get_font_faces(font_variant_folder)
            if face.family == "RenderCV Variant Test" and face.style == "italic"
        )
        assert faces
        assert (
            resolve_font_weight(
                "RenderCV Variant Test", faces, None, "thin", font_weight_names
            )
            == 280
        )

    def test_style_matching_takes_priority_over_stretch(self, font_variant_folder):
        (font_variant_folder / "Variant-400.ttf").unlink()
        faces = tuple(
            face
            for face in get_font_faces(font_variant_folder)
            if face.family == "RenderCV Variant Test"
        )
        assert (
            resolve_font_weight(
                "RenderCV Variant Test", faces, 300, None, font_weight_names
            )
            == 300
        )
        with pytest.raises(ValueError, match="does not provide weight 280"):
            resolve_font_weight(
                "RenderCV Variant Test", faces, 280, None, font_weight_names
            )
        source = b'#set text(font: "RenderCV Variant Test", weight: 280)\nSample text'
        pdf = typst.compile(
            source, font_paths=[font_variant_folder], ignore_system_fonts=True
        )
        assert isinstance(pdf, bytes)
        assert b"RenderCVVariantTest-300" in pdf

    @pytest.mark.parametrize("upright", [True, False])
    def test_uses_variable_upright_instances_for_matching(
        self, font_settings_folder, font_variant_folder, upright
    ):
        path = font_variant_folder / "Variant-280.ttf"
        with (
            TTFont(font_settings_folder / "Variable.ttf") as source,
            TTFont(path) as font,
        ):
            font["fvar"] = source["fvar"]
            axis = Axis()
            axis.axisTag = "ital"
            axis.minValue = 0 if upright else 0.2
            axis.defaultValue = 1
            axis.maxValue = 1
            axis.flags = 0
            axis.axisNameID = font["name"].addName("Italic")
            font["fvar"].axes.append(axis)
            for instance in font["fvar"].instances:
                instance.coordinates["ital"] = 1
            font.save(path)
        faces = tuple(
            face
            for face in get_font_faces(font_variant_folder)
            if face.family == "RenderCV Variant Test"
        )
        if upright:
            assert (
                resolve_font_weight(
                    "RenderCV Variant Test", faces, 350, None, font_weight_names
                )
                == 350
            )
        else:
            with pytest.raises(ValueError, match="does not provide weight 350"):
                resolve_font_weight(
                    "RenderCV Variant Test", faces, 350, None, font_weight_names
                )
