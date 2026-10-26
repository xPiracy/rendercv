import functools
import pathlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import typst


@dataclass(frozen=True)
class FontMetadata:
    """Weights and named styles available in one discovered font face."""

    weight: int
    names: tuple[str, ...]
    weight_range: tuple[float, float] | None = None
    named_weights: tuple[tuple[str, int], ...] = ()
    upright_instance: bool = False


def normalize_subfamily_name(name: str) -> str:
    """Normalize font subfamily names while keeping weight and italic separate.

    Args:
        name: Subfamily or named instance from a font's name table.

    Returns:
        Lowercase weight name with style suffixes and separators removed.
    """
    normalized = name.lower().replace(" ", "").replace("-", "")
    normalized = normalized.replace("italic", "").replace("oblique", "")
    if normalized in {"", "normal", "roman", "book"}:
        return "regular"
    return normalized


@functools.lru_cache(maxsize=8)
def discover_font_faces(
    user_font_folder: pathlib.Path,
    _signature: tuple[tuple[str, int, int], ...],
) -> tuple["typst.FontInfo", ...]:
    """Discover the same bundled, system and local fonts used by rendering.

    Args:
        user_font_folder: The fonts folder next to the input YAML.
        _signature: File states that invalidate cached local font discovery.

    Returns:
        Font faces discovered by Typst, including embedded fonts.

    Raises:
        ValueError: Optional rendering dependencies are unavailable.
    """
    try:
        # Rendering dependencies are optional for the schema-only installation.
        import rendercv_fonts  # noqa: PLC0415
        import typst  # noqa: PLC0415
    except ImportError as error:
        raise ValueError(
            "Font settings validation requires the rendering dependencies."
            " Install rendercv[full]."
        ) from error

    return tuple(
        typst.Fonts(
            font_paths=[*rendercv_fonts.paths_to_font_folders, user_font_folder]
        ).fonts()
    )


def get_font_faces(user_font_folder: pathlib.Path) -> tuple["typst.FontInfo", ...]:
    """Discover fonts, refreshing when local font files change.

    Args:
        user_font_folder: The fonts folder next to the input YAML.

    Returns:
        Font faces available to the renderer.
    """
    signature = tuple(
        (str(path), path.stat().st_mtime_ns, path.stat().st_size)
        for path in sorted(user_font_folder.rglob("*"))
        if path.is_file() and path.suffix.lower() in {".ttf", ".otf", ".ttc", ".otc"}
    )
    return discover_font_faces(user_font_folder, signature)


@functools.lru_cache(maxsize=256)
def read_font_metadata(
    path: pathlib.Path,
    index: int,
    weight: int,
    _modified: int,
    _size: int,
    style: str = "normal",
) -> FontMetadata:
    """Read subfamilies and variable weights without modifying the font.

    Args:
        path: Font file discovered by Typst.
        index: Face index for font collections.
        weight: Face weight reported by Typst.
        _modified: Modification time used to invalidate cached metadata.
        _size: File size used to invalidate cached metadata.
        style: Source style reported by Typst.

    Returns:
        Actual face weight, subfamily and variable weight information.

    Raises:
        ValueError: Font metadata cannot be read.
    """
    try:
        # Rendering dependencies are optional for the schema-only installation.
        from fontTools.ttLib import TTFont, TTLibError  # noqa: PLC0415
    except ImportError as error:
        raise ValueError(
            "Font weight validation requires fontTools. Install rendercv[full]."
        ) from error

    try:
        with TTFont(path, fontNumber=index, lazy=True) as font:
            name_table = font["name"]
            subfamily = name_table.getDebugName(17) or name_table.getDebugName(2)
            names = (normalize_subfamily_name(subfamily),) if subfamily else ()
            weight_range = None
            named_weights: list[tuple[str, int]] = []
            upright_instance = False
            if "fvar" in font:
                variable = font["fvar"]
                axes = {axis.axisTag: axis for axis in variable.axes}
                style_axis = {"italic": "ital", "oblique": "slnt"}.get(style)
                upright_instance = style_axis in axes and all(
                    axes[tag].minValue <= 0 <= axes[tag].maxValue
                    for tag in ("ital", "slnt")
                    if tag in axes
                )
                weight_axis = next(
                    (axis for axis in variable.axes if axis.axisTag == "wght"), None
                )
                if weight_axis is not None:
                    weight_range = (weight_axis.minValue, weight_axis.maxValue)
                    for instance in variable.instances:
                        name = name_table.getDebugName(instance.subfamilyNameID)
                        coordinate = instance.coordinates.get("wght")
                        if (
                            name
                            and coordinate is not None
                            and float(coordinate).is_integer()
                        ):
                            named_weights.append(
                                (normalize_subfamily_name(name), int(coordinate))
                            )
            return FontMetadata(
                weight, names, weight_range, tuple(named_weights), upright_instance
            )
    except (OSError, TTLibError, KeyError) as error:
        message = f"Cannot read font weight metadata from {path.name}."
        raise ValueError(message) from error


def get_face_metadata(face: "typst.FontInfo") -> FontMetadata:
    """Read a discovered face, using Typst's weights for embedded fonts.

    Args:
        face: A face from Typst's font discovery.

    Returns:
        Weight metadata for the face.
    """
    if face.path is None:
        return FontMetadata(face.weight, ())
    path = pathlib.Path(face.path)
    stat = path.stat()
    return read_font_metadata(
        path, face.index, face.weight, stat.st_mtime_ns, stat.st_size, style=face.style
    )


def resolve_font_weight(
    family: str,
    faces: tuple["typst.FontInfo", ...],
    weight: int | None,
    weight_name: str | None,
    canonical_weights: dict[str, int],
) -> int | None:
    """Resolve weights supported by the family's effective upright variants.

    Why:
        Typst matches style and stretch before weight. A weight available only
        in a less suitable variant would silently select a different weight.

    Args:
        family: The validated family name.
        faces: Faces belonging to the family.
        weight: Exact numeric weight requested by the user.
        weight_name: Named style requested by the user.
        canonical_weights: Conventional names for embedded Typst face weights.

    Returns:
        The actual available weight or None when neither selector is set.

    Raises:
        ValueError: The family does not provide the requested weight or name.
    """
    if weight is None and weight_name is None:
        return None

    metadata = tuple((face, get_face_metadata(face)) for face in faces)
    upright = tuple(
        (face, data)
        for face, data in metadata
        if face.style == "normal" or data.upright_instance
    )
    metadata = upright or metadata
    if metadata:
        nearest_stretch = min(abs(face.stretch - 1) for face, _ in metadata)
        metadata = tuple(
            (face, data)
            for face, data in metadata
            if abs(face.stretch - 1) == nearest_stretch
        )
    if weight is not None:
        if any(
            weight == data.weight
            or (
                data.weight_range is not None
                and data.weight_range[0] <= weight <= data.weight_range[1]
            )
            for _, data in metadata
        ):
            return weight
        available = ", ".join(
            str(value) for value in sorted({face.weight for face, _ in metadata})
        )
        message = (
            f"Font family '{family}' does not provide weight {weight}."
            f" Available face weights: {available}."
        )
        raise ValueError(message)

    assert weight_name is not None
    named_weights = {
        named_weight
        for _, data in metadata
        for name, named_weight in data.named_weights
        if name == weight_name
    }
    named_weights.update(
        data.weight
        for _, data in metadata
        if weight_name in data.names
        and not any(name == weight_name for name, _ in data.named_weights)
    )
    named_weights.update(
        face.weight
        for face, _ in metadata
        if face.path is None and face.weight == canonical_weights[weight_name]
    )
    if len(named_weights) == 1:
        named_weight = named_weights.pop()
        if not 100 <= named_weight <= 900:
            message = (
                f"Font family '{family}' has named '{weight_name}' weight"
                f" {named_weight}, outside Typst's supported range of 100 to 900."
            )
            raise ValueError(message)
        return named_weight
    if named_weights:
        message = (
            f"Font family '{family}' has more than one '{weight_name}' weight."
            " Select its numeric weight instead."
        )
        raise ValueError(message)
    message = (
        f"Font family '{family}' does not provide a named '{weight_name}' weight."
        " Select an available named style or an exact numeric weight instead."
    )
    raise ValueError(message)
