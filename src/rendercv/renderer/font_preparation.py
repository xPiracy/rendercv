import atexit
import functools
import math
import pathlib
import shutil
import tempfile
from dataclasses import dataclass
from typing import Protocol, cast

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

from rendercv.schema.models.design.font_metadata import get_font_faces
from rendercv.schema.models.design.font_settings import FontSettings
from rendercv.schema.models.rendercv_model import RenderCVModel


class FontWeightTable(Protocol):
    """Weight and style fields dynamically populated by fontTools."""

    usWeightClass: int
    usWidthClass: int
    fsSelection: int


class FontStyleTable(Protocol):
    """Style field dynamically populated by fontTools."""

    macStyle: int


@dataclass(frozen=True)
class FontSource:
    """A discovered font face and the file state used to cache prepared fonts."""

    path: pathlib.Path
    index: int
    family: str
    style: str
    weight: int
    modified: int
    size: int


def requested_font_weights(
    model: RenderCVModel,
) -> tuple[tuple[str, tuple[int, ...]], ...]:
    """Collect weights needed by roles that explicitly select a font weight.

    Args:
        model: CV model containing per-role font settings.

    Returns:
        Family names and weights, including legacy and native strong fallbacks.
    """
    typography = model.design.typography
    roles = ("body", "name", "headline", "connections", "section_titles")
    families: dict[str, set[int]] = {}
    for role in roles:
        font = getattr(typography.font_family, role)
        if isinstance(font, FontSettings) and (
            font.resolved_weight is not None or font.resolved_bold_weight is not None
        ):
            families.setdefault(font.family.casefold(), {400, 700, 900})

    for role in roles:
        font = getattr(typography.font_family, role)
        family = font.family if isinstance(font, FontSettings) else font
        if family.casefold() not in families:
            continue
        explicit_weight = (
            font.resolved_weight if isinstance(font, FontSettings) else None
        )
        bold_weight = (
            font.resolved_bold_weight if isinstance(font, FontSettings) else None
        )
        legacy_bold = role != "body" and getattr(typography.bold, role)
        base_weight = explicit_weight
        if base_weight is None:
            base_weight = (bold_weight or 700) if legacy_bold else 400
        strong_weight = bold_weight or min(base_weight + 300, 900)
        families[family.casefold()].update(
            (base_weight, strong_weight, min(strong_weight + 300, 900))
        )
    return tuple(
        (family, tuple(sorted(weights))) for family, weights in sorted(families.items())
    )


def prepare_font_directory(model: RenderCVModel) -> pathlib.Path | None:
    """Prepare static instances when explicit controls select a variable font.

    Why:
        The bundled Typst compiler cannot interpolate variable fonts. Static
        instances let it render exact requested coordinates. A replacement font
        directory excludes the source variable files so they cannot win matching.
        Ordinary static fonts and omitted weight controls keep the existing path.

    Args:
        model: CV model with font selections and its input YAML location.

    Returns:
        Temporary replacement font directory, or None when no instances are needed.
    """
    requests = requested_font_weights(model)
    if not requests:
        return None
    user_folder = (
        model._input_file_path.parent if model._input_file_path else pathlib.Path.cwd()
    ) / "fonts"
    faces = get_font_faces(user_folder.resolve())
    sources: list[FontSource] = []
    variable_faces: set[tuple[pathlib.Path, int]] = set()
    selected_families = {family for family, _ in requests}
    for face in faces:
        if face.path is None:
            continue
        path = pathlib.Path(face.path)
        stat = path.stat()
        sources.append(
            FontSource(
                path,
                face.index,
                face.family,
                face.style,
                face.weight,
                stat.st_mtime_ns,
                stat.st_size,
            )
        )
        if face.family.casefold() in selected_families:
            with TTFont(path, fontNumber=face.index, lazy=True) as font:
                if "fvar" in font:
                    variable_faces.add((path, face.index))
    if not variable_faces:
        return None
    return materialize_font_directory(
        tuple(sources), tuple(sorted(variable_faces)), requests
    )


@functools.lru_cache(maxsize=8)
def materialize_font_directory(
    sources: tuple[FontSource, ...],
    variable_faces: tuple[tuple[pathlib.Path, int], ...],
    requests: tuple[tuple[str, tuple[int, ...]], ...],
) -> pathlib.Path:
    """Build a cached font directory without changing the discovered source fonts.

    Args:
        sources: All discovered file-backed faces, including file signatures.
        variable_faces: Faces that require static instancing.
        requests: Required weights for each selected family.

    Returns:
        Directory of unchanged font links and prepared static instances.
    """
    folder = pathlib.Path(tempfile.mkdtemp(prefix="rendercv-fonts-"))
    atexit.register(shutil.rmtree, str(folder), True)
    replaced_paths = {path for path, _ in variable_faces}
    variable_set = set(variable_faces)
    weights = dict(requests)
    linked_paths: set[pathlib.Path] = set()
    for number, source in enumerate(sources):
        if source.path not in replaced_paths:
            if source.path in linked_paths:
                continue
            destination = folder / f"source-{number}{source.path.suffix}"
            try:
                destination.hardlink_to(source.path)
            except OSError:
                shutil.copyfile(source.path, destination)
            linked_paths.add(source.path)
            continue
        with TTFont(
            source.path, fontNumber=source.index, recalcTimestamp=False
        ) as font:
            if (source.path, source.index) not in variable_set:
                # Preserve other faces when a collection contains a selected face.
                suffix = ".otf" if font.sfntVersion == "OTTO" else ".ttf"
                font.save(folder / f"source-{number}{suffix}")
                continue
            for coordinate, style, location in font_instance_locations(
                font, source.style, source.weight, weights[source.family.casefold()]
            ):
                instance = instantiateVariableFont(
                    font,
                    location,
                    inplace=False,
                    updateFontNames=False,
                    downgradeCFF2="CFF2" in font,
                    static=True,
                )
                # Pinning wdth can rewrite its matching category. Retain the
                # source face's category so validation and font matching agree.
                cast(FontWeightTable, instance["OS/2"]).usWidthClass = cast(
                    FontWeightTable, font["OS/2"]
                ).usWidthClass
                name_font_instance(instance, source.family, coordinate, style, number)
                suffix = ".otf" if instance.sfntVersion == "OTTO" else ".ttf"
                instance.save(
                    folder / f"instance-{number}-{coordinate}-{style}{suffix}"
                )
                instance.close()
    return folder


def font_instance_locations(
    font: TTFont, style: str, weight: int, requested_weights: tuple[int, ...]
) -> list[tuple[int, str, dict[str, float]]]:
    """Pin every variation axis, retaining real italic and oblique variants.

    Args:
        font: Variable font to instance.
        style: Style discovered from the source face.
        weight: Default face weight discovered by Typst.
        requested_weights: Weights needed by roles using this family.

    Returns:
        Weight, style and pinned variation coordinates for each static instance.
    """
    axes = {axis.axisTag: axis for axis in font["fvar"].axes}
    defaults = {tag: axis.defaultValue for tag, axis in axes.items()}
    can_reset_italic = (
        "ital" not in axes or axes["ital"].minValue <= 0 <= axes["ital"].maxValue
    )
    can_reset_slant = (
        "slnt" not in axes or axes["slnt"].minValue <= 0 <= axes["slnt"].maxValue
    )
    has_style_axis = "ital" in axes or "slnt" in axes
    can_be_upright = style != "italic" or "ital" in axes
    upright = defaults | {tag: 0.0 for tag in ("ital", "slnt") if tag in axes}
    styles: list[tuple[str, dict[str, float]]] = []
    if has_style_axis and can_be_upright and can_reset_italic and can_reset_slant:
        styles.append(("normal", upright))
    if "ital" in axes and axes["ital"].minValue <= 1 <= axes["ital"].maxValue:
        styles.append(("italic", defaults | {"ital": 1.0}))
    if "slnt" in axes and can_be_upright and can_reset_italic:
        axis = axes["slnt"]
        slant = axis.minValue if axis.minValue < 0 else axis.maxValue
        if slant != 0:
            styles.append(("oblique", upright | {"slnt": slant}))
    if not styles:
        styles = [(style, defaults)]
    coordinates = requested_weights if "wght" in axes else (weight,)
    result: list[tuple[int, str, dict[str, float]]] = []
    for coordinate in coordinates:
        location_weight = float(coordinate)
        instance_weight = coordinate
        if "wght" in axes:
            axis = axes["wght"]
            if coordinate < axis.minValue:
                location_weight = axis.minValue
                instance_weight = math.floor(axis.minValue)
            elif coordinate > axis.maxValue:
                location_weight = axis.maxValue
                instance_weight = math.ceil(axis.maxValue)
        for instance_style, location in styles:
            pinned_location = location | (
                {"wght": location_weight} if "wght" in axes else {}
            )
            item = (instance_weight, instance_style, pinned_location)
            if item not in result:
                result.append(item)
    return result


def name_font_instance(
    font: TTFont, family: str, weight: int, style: str, number: int
) -> None:
    """Give a temporary instance consistent family, weight and style metadata.

    Args:
        font: Prepared static font, changed only in memory.
        family: Family name recognised by Typst for the source font.
        weight: Selected numeric weight.
        style: Normal, italic or oblique style represented by its real outlines.
        number: Source index used to keep PostScript names unique.

    Returns:
        None. Updates the temporary instance's naming and matching metadata.
    """
    subfamily = {400: "Regular", 700: "Bold"}.get(weight, f"Weight {weight}")
    if style != "normal":
        subfamily += " " + style.title()
    names = {
        1: family,
        2: subfamily,
        4: family + " " + subfamily,
        6: f"RenderCVInstance{number}W{weight}{style.title()}",
        16: family,
        17: subfamily,
    }
    name_table = font["name"]
    name_table.names = [
        record for record in name_table.names if record.nameID not in names
    ]
    for name_id, value in names.items():
        name_table.setName(value, name_id, 3, 1, 0x409)
    os2 = cast(FontWeightTable, font["OS/2"])
    os2.usWeightClass = weight
    selection = os2.fsSelection
    selection &= ~((1 << 0) | (1 << 5) | (1 << 6) | (1 << 9))
    if weight >= 700:
        selection |= 1 << 5
    elif weight == 400 and style == "normal":
        selection |= 1 << 6
    if style == "italic":
        selection |= 1 << 0
    elif style == "oblique":
        selection |= 1 << 9
    os2.fsSelection = selection
    head = cast(FontStyleTable, font["head"])
    head.macStyle = (1 if weight >= 700 else 0) | (2 if style == "italic" else 0)
