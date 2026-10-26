# `design` Field

The `design` field controls every visual aspect of your CV: colors, fonts, spacing, and layout.

## Built-in Themes

RenderCV includes << theme_count >> built-in themes. To use one, simply specify the theme:

```yaml
design:
  theme: classic
```

Available themes: << available_themes >>.

All themes are identical except for their default values. If you specify a setting explicitly, it overrides the theme's default. This means:

- If you specify all design options in your YAML, changing the theme has no effect
- If you leave settings unspecified, changing the theme completely changes the design (because it uses different defaults)
- You can start with any theme and customize only what you want to change

## Customizing Design

You can override any field to fine-tune the theme:

```yaml
design:
  theme: classic
  colors:
    name: rgb(255, 0, 0)  # Override just the name color
```

Or specify all options for complete control:

```yaml
design:
  theme: classic

  page:
    size: us-letter # (1)!
    top_margin: 0.7in
    bottom_margin: 0.7in
    left_margin: 0.7in
    right_margin: 0.7in
    show_footer: true
    show_top_note: true

  colors:
    body: rgb(0, 0, 0)
    name: rgb(0, 79, 144)
    headline: rgb(0, 79, 144)
    connections: rgb(0, 79, 144)
    section_titles: rgb(0, 79, 144)
    links: rgb(0, 79, 144)
    footer: rgb(128, 128, 128)
    top_note: rgb(128, 128, 128)

  typography:
    line_spacing: 0.6em
    alignment: justified # (2)!
    date_and_location_column_alignment: right
    font_family: # (11)!
      body: Source Sans 3 # (9)!
      name: Source Sans 3
      headline: Source Sans 3
      connections: Source Sans 3
      section_titles: Source Sans 3
    font_size:
      body: 10pt
      name: 30pt
      headline: 10pt
      connections: 10pt
      section_titles: 1.4em
    small_caps:
      name: false
      headline: false
      connections: false
      section_titles: false
    bold:
      name: true
      headline: false
      connections: false
      section_titles: true

  links:
    underline: false
    show_external_link_icon: false

  header:
    alignment: center # (3)!
    photo_width: 3.5cm
    photo_position: left # (8)!
    photo_space_left: 0.4cm
    photo_space_right: 0.4cm
    space_below_name: 0.7cm
    space_below_headline: 0.7cm
    space_below_connections: 0.7cm
    connections:
      phone_number_format: national # (7)!
      hyperlink: true
      show_icons: true
      display_urls_instead_of_usernames: false
      separator: ''
      space_between_connections: 0.5cm

  section_titles:
    type: with_partial_line # (4)!
    line_thickness: 0.5pt
    space_between_text_and_line: null
    space_above: 0.5cm
    space_below: 0.3cm

  sections:
    allow_page_break: true
    space_between_regular_entries: 1.2em
    space_between_text_based_entries: 0.3em
    show_time_spans_in: # (5)!
      - experience

  entries:
    date_and_location_width: 4.15cm
    side_space: 0.2cm
    space_between_columns: 0.1cm
    allow_page_break: false
    short_second_row: true
    summary:
      space_above: 0cm
      space_left: 0cm
    highlights:
      bullet: • # (6)!
      nested_bullet: •
      space_left: 0.15cm
      space_above: 0cm
      space_between_items: 0cm
      space_between_bullet_and_text: 0.5em

  templates: # (10)!
    footer: '*NAME -- PAGE_NUMBER/TOTAL_PAGES*'
    top_note: '*LAST_UPDATED CURRENT_DATE*'
    single_date: MONTH_ABBREVIATION YEAR
    date_range: START_DATE – END_DATE
    time_span: HOW_MANY_YEARS YEARS HOW_MANY_MONTHS MONTHS
    one_line_entry:
      main_column: '**LABEL:** DETAILS'
    education_entry:
      main_column: |-
        **INSTITUTION**, AREA
        SUMMARY
        HIGHLIGHTS
      degree_column: '**DEGREE**'
      date_and_location_column: |-
        LOCATION
        DATE
    normal_entry:
      main_column: |-
        **NAME**
        SUMMARY
        HIGHLIGHTS
      date_and_location_column: |-
        LOCATION
        DATE
    experience_entry:
      main_column: |-
        **COMPANY**, POSITION
        SUMMARY
        HIGHLIGHTS
      date_and_location_column: |-
        LOCATION
        DATE
    publication_entry:
      main_column: |-
        **TITLE**
        AUTHORS
        URL (JOURNAL)
      date_and_location_column: DATE
```

1. **Page size options:** << available_page_sizes >>
2. **Body text alignment:** << available_body_alignments >>
   `justified` spreads text across the full width, `justified-with-no-hyphenation` does the same without breaking words
3. **Header alignment:** << available_alignments >>
4. **Section title styles:** << available_section_title_types >>
   `with_partial_line` adds a line next to the title, `with_full_line` spans the page, `without_line` has no line, `moderncv` uses ModernCV style, `centered_without_line` centers the title with no line, `centered_with_partial_line` centers with baseline partial lines on both sides, `centered_with_centered_partial_line` centers with middle-aligned lines on both sides, `centered_with_full_line` centers with a full line underneath
5. **Show time spans:** Specify which sections should display duration calculations (e.g., "2 years 3 months")
6. **Bullet characters:** << available_bullets >>
7. **Phone number formats:** << available_phone_number_formats >>
   `national` formats for domestic use, `international` includes country code, `E164` is the standard international format
8. **Photo position:** `left` or `right` of the header text
9. **Available fonts:** << available_font_families >>. Also, any system font can be used. Custom fonts can be used as well. See [Custom Fonts](../how_to/custom_fonts.md) for more information.
10. **Templates:** Advanced customization - define how each entry type is rendered using placeholders like NAME, COMPANY, DATE, etc.
11. **Font family shorthand:** You can specify `font_family: "Latin Modern Roman"` directly instead of using nested options to apply the same font everywhere

## Font Weights and Letter Spacing

Each `typography.font_family` role accepts either a family name or an object with optional weight and spacing controls. The roles are `body`, `name`, `headline`, `connections`, and `section_titles`. You can mix strings and objects; each object's controls apply only to its role.

For example, with an Inter variable font that supports weights 350 and 650 available to RenderCV:

```yaml
design:
  typography:
    font_family:
      body:
        family: Inter
        weight: 350
        bold_weight: 650
        letter_spacing: default
      name: Source Sans 3
      section_titles:
        family: Source Sans 3
        weight_name: semibold
        letter_spacing: 1.05
```

`family` is required in an object. All other fields are optional. A string such as `body: Inter`, or an object containing only `family: Inter`, keeps the existing weight and spacing behaviour.

| Field | Accepted values | Purpose |
| --- | --- | --- |
| `family` | Font family name | Selects the family using its font metadata name. |
| `weight` | Integer from 100 to 900 | Sets the role's base weight. Values such as 280, 350, or 450 are allowed when supported by the font. |
| `weight_name` | An available weight name from the table below | Selects the font's named face or variable instance instead of a numeric `weight`. |
| `bold_weight` | Integer from 100 to 900 | Sets the weight used for bold text within the role. |
| `bold_weight_name` | An available weight name from the table below | Selects the named bold face or instance instead of a numeric `bold_weight`. |
| `letter_spacing` | `default`, `null`, a positive number, or a length such as `0.03em` | Controls additional spacing between characters. |

Use `weight` or `weight_name`, and `bold_weight` or `bold_weight_name`. Supplying non-null values for both selectors in either pair is an error. Weight numbers must be integers; values such as `350.5` or `true` are rejected.

### Weight Names

| Name | Conventional weight |
| --- | --- |
| `thin` | 100 |
| `extralight` | 200 |
| `light` | 300 |
| `regular` | 400 |
| `medium` | 500 |
| `semibold` | 600 |
| `bold` | 700 |
| `extrabold` | 800 |
| `black` | 900 |

Readable aliases such as `extra light`, `semi bold`, and `extra bold` are also accepted. A named selector must match an available face or variable instance in the selected family. RenderCV uses its actual metadata weight, which can differ from the conventional value in the table: a font's Thin face could have weight 280. An unavailable name is an error; it does not create a missing face or silently select the nearest weight.

For a variable weight without a named instance, use a numeric selector within the font's supported range.

Typst's embedded fonts do not expose their source name records. For those fonts only, names use the conventional values above and must match an available face weight.

### Bold Text

An explicit `weight` or `weight_name` takes precedence over the role's existing `typography.bold` flag. Without an explicit base weight, that flag keeps its usual behaviour: regular text uses 400, and bold text uses `bold_weight` when supplied or 700 otherwise.

`bold_weight` also controls inline Markdown `**bold text**` within the role. It selects that absolute weight, so `weight: 350` with `bold_weight: 650` produces base text at 350 and bold text at 650. Omitting the bold selector preserves Typst's usual relative strong emphasis.

### Character Spacing

Omit `letter_spacing`, use `default` or `null`, or set it to `1` to keep the font's native spacing and kerning. A numeric factor adds tracking equal to `(factor - 1)em`: `1.05` adds `0.05em` between characters, while `0.98` subtracts `0.02em`. This adds a fixed amount based on the font size; it does not multiply each glyph's width. Numeric factors must be positive and finite.

You can also provide a length directly, such as `letter_spacing: 0.03em` or `letter_spacing: -0.01em`. An `em` is the current font size, so `0.03em` adds 0.3pt at a 10pt text size.

### Available Font Faces

Use the family name stored in the font's metadata, with its normal spaces. Put custom `.ttf` or `.otf` files in the `fonts` directory next to your YAML file; see [Custom Fonts](../how_to/custom_fonts.md).

A static font file usually provides one face at one weight. To select several weights, supply the matching files from the same family or a variable font whose `wght` axis supports the requested values. One `.otf` file does not necessarily contain every weight or an italic face. True italics require a matching italic face or an italic variation axis; these weight and spacing controls do not add italic glyphs.

Font objects validate the family and any explicit weight against the available font files. An unknown family, a missing named face, or a numeric weight outside the available static weights or variable range causes an error. Existing family-name strings keep their previous matching behaviour.

Weight validation follows Typst's matching order for normal text: upright faces take priority over italic or oblique faces, then stretch closest to normal takes priority over weight. A weight available only in a lower-priority face is rejected. When no upright face exists, Typst's native style fallback applies. A variable font can provide an upright face through an `ital: 0` or `slnt: 0` coordinate when its axes support those values. Inline italics keep Typst's native face matching.

For variable fonts, RenderCV supplies temporary static instances to its PDF and PNG compiler without changing the source font files. A standalone exported `.typ` file needs usable static font files or an external compiler that supports variable fonts. Use the updated bundled RenderCV Typst library for standalone compilation with these settings; the published `@preview/rendercv:0.3.0` package does not include these arguments.

## Space Between Section Titles and Lines

For `centered_with_partial_line` and `centered_with_centered_partial_line`, set `section_titles.space_between_text_and_line` to control the horizontal gap between the title text and the line on each side:

```yaml
design:
  section_titles:
    type: centered_with_centered_partial_line
    space_between_text_and_line: 0.4em
```

This field accepts a length such as `0.4em`, `3pt`, or `0.1cm`. Omit it or use `null` to keep the existing `0.3em` gap. Other section title styles are unaffected.
