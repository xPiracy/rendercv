import pathlib
from decimal import Decimal
from typing import Annotated, Literal, Self

import pydantic

from ..base import BaseModelWithoutExtraKeys
from ..validation_context import get_input_file_path
from .font_family import FontFamily, available_font_families
from .font_metadata import get_font_faces, resolve_font_weight
from .typst_dimension import TypstDimension

font_weight_names: dict[str, int] = {
    "thin": 100,
    "extralight": 200,
    "light": 300,
    "regular": 400,
    "medium": 500,
    "semibold": 600,
    "bold": 700,
    "extrabold": 800,
    "black": 900,
}
font_weight_aliases: list[str] = [
    *font_weight_names,
    "extra light",
    "extra-light",
    "semi bold",
    "semi-bold",
    "extra bold",
    "extra-bold",
]
font_weight_name_pattern: str = (
    r"^\s*(?:"
    + "|".join(
        "".join(
            f"[{letter}{letter.upper()}]" if letter.isalpha() else letter
            for letter in name
        )
        for name in font_weight_aliases
    )
    + r")\s*$"
)


def normalize_font_weight_name(value: object) -> object:
    """Normalize readable weight names before validating the canonical names.

    Args:
        value: Weight name supplied in YAML.

    Returns:
        Lowercase weight name without spaces or hyphens.
    """
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in font_weight_aliases:
            return normalized.replace(" ", "").replace("-", "")
    return value


type FontWeightName = Annotated[
    Literal[
        "thin",
        "extralight",
        "light",
        "regular",
        "medium",
        "semibold",
        "bold",
        "extrabold",
        "black",
    ],
    pydantic.BeforeValidator(normalize_font_weight_name),
    pydantic.WithJsonSchema(
        {
            "type": "string",
            "pattern": font_weight_name_pattern,
            "examples": font_weight_aliases,
        }
    ),
]
type FontWeight = Annotated[int, pydantic.Field(strict=True, ge=100, le=900)]
type SpacingDimension = Annotated[
    TypstDimension,
    pydantic.WithJsonSchema(
        {
            "type": "string",
            "pattern": r"^-?\d+(?:\.\d+)?(cm|in|pt|mm|em)(?![\s\S])",
        }
    ),
]
type LetterSpacing = (
    Literal["default"]
    | Annotated[float, pydantic.Field(strict=True, gt=0, allow_inf_nan=False)]
    | SpacingDimension
)


class FontSettings(BaseModelWithoutExtraKeys):
    """Optional font controls for one typography role.

    Why:
        A family string keeps the existing font selection. This object adds
        explicit controls only when a user requests them.
    """

    model_config = pydantic.ConfigDict(
        json_schema_extra={
            "allOf": [
                {
                    "not": {
                        "required": [numeric, named],
                        "properties": {
                            numeric: {"not": {"type": "null"}},
                            named: {"not": {"type": "null"}},
                        },
                    }
                }
                for numeric, named in (
                    ("weight", "weight_name"),
                    ("bold_weight", "bold_weight_name"),
                )
            ]
        }
    )

    family: Annotated[
        FontFamily,
        pydantic.WithJsonSchema(
            {"type": "string", "examples": available_font_families}
        ),
    ] = pydantic.Field(
        description="The font family name recorded in the font metadata.",
    )
    weight: FontWeight | None = pydantic.Field(
        default=None,
        description=(
            "An exact integer font weight between 100 and 900. Use either weight"
            " or weight_name. Omit both to preserve the theme's weight selection."
        ),
    )
    weight_name: FontWeightName | None = pydantic.Field(
        default=None,
        description=(
            "A named font weight: thin, extralight, light, regular, medium,"
            " semibold, bold, extrabold, or black. Names are case-insensitive;"
            " extra light, semi bold, and extra bold also accept spaces or hyphens."
            " The name must match an available font subfamily or named variable"
            " instance; its metadata determines the numeric weight. Use either"
            " weight_name or weight."
        ),
    )
    bold_weight: FontWeight | None = pydantic.Field(
        default=None,
        description=(
            "An exact integer weight for bold text between 100 and 900, including"
            " Markdown bold text. Use either bold_weight or bold_weight_name."
            " Omit both to preserve the theme's bold selection."
        ),
    )
    bold_weight_name: FontWeightName | None = pydantic.Field(
        default=None,
        description=(
            "A named weight for bold text, including Markdown bold text. Accepts"
            " the same names as weight_name. Use either bold_weight_name or"
            " bold_weight."
        ),
    )
    letter_spacing: LetterSpacing | None = pydantic.Field(
        default=None,
        description=(
            "Extra tracking between characters. Use default or null to preserve"
            " font spacing, a positive finite factor (1 preserves spacing; 1.05"
            " adds 0.05em), or a Typst length such as 0.03em or -0.01em. Factors"
            " add em tracking while retaining kerning; they do not scale glyph"
            " advances."
        ),
    )

    _resolved_weight: int | None = pydantic.PrivateAttr(default=None)
    _resolved_bold_weight: int | None = pydantic.PrivateAttr(default=None)

    @pydantic.model_validator(mode="after")
    def validate_weight_selectors(self, info: pydantic.ValidationInfo) -> Self:
        """Reject conflicting selectors and resolve actual available font weights.

        Args:
            info: Validation context for locating user fonts.

        Returns:
            Settings with an unambiguous selector for each weight.

        Raises:
            ValueError: Selectors conflict or the requested font is unavailable.
        """
        if self.weight is not None and self.weight_name is not None:
            raise ValueError("Use either weight or weight_name, not both.")
        if self.bold_weight is not None and self.bold_weight_name is not None:
            raise ValueError("Use either bold_weight or bold_weight_name, not both.")

        input_file_path = get_input_file_path(info)
        user_font_folder = (
            input_file_path.parent if input_file_path else pathlib.Path.cwd()
        ) / "fonts"
        faces = tuple(
            face
            for face in get_font_faces(user_font_folder.resolve())
            if face.family.casefold() == self.family.casefold()
        )
        if not faces:
            message = (
                f"Font family '{self.family}' is not available. Use its metadata"
                " family name and install it or place its files in the fonts"
                " folder next to your input YAML."
            )
            raise ValueError(message)
        self._resolved_weight = resolve_font_weight(
            self.family, faces, self.weight, self.weight_name, font_weight_names
        )
        self._resolved_bold_weight = resolve_font_weight(
            self.family,
            faces,
            self.bold_weight,
            self.bold_weight_name,
            font_weight_names,
        )
        return self

    @property
    def resolved_weight(self) -> int | None:
        """Return the requested base weight, leaving omitted selection unchanged."""
        return self._resolved_weight

    @property
    def resolved_bold_weight(self) -> int | None:
        """Return the requested bold weight, leaving omitted selection unchanged."""
        return self._resolved_bold_weight

    @property
    def resolved_tracking(self) -> str | None:
        """Return Typst tracking, omitting default and identity-factor settings."""
        spacing = self.letter_spacing
        if spacing is None or spacing == "default" or spacing == 1:
            return None
        if isinstance(spacing, str):
            return spacing
        return f"{Decimal(str(spacing)) - Decimal(1):f}em"

    def __str__(self) -> str:
        """Return the family name for templates that only consume family names."""
        return self.family
