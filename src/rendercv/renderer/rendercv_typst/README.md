A CV/resume typesetting package for academics and engineers. Part of [RenderCV](https://github.com/rendercv/rendercv).

All six looks below are produced by the same package with different parameter values.

<table>
<tr>
<td><img alt="Example CV using the Classic theme with blue accents and partial section title lines" src="https://raw.githubusercontent.com/rendercv/rendercv/9b7830a0e1b5d731461320c10df0a9c12267e5f0/docs/assets/images/examples/classic.png" width="350"></td>
<td><img alt="Example CV using the Engineering Resumes theme with a minimal single-column layout" src="https://raw.githubusercontent.com/rendercv/rendercv/9b7830a0e1b5d731461320c10df0a9c12267e5f0/docs/assets/images/examples/engineeringresumes.png" width="350"></td>
<td><img alt="Example CV using the Sb2nov theme with full-width section title lines" src="https://raw.githubusercontent.com/rendercv/rendercv/9b7830a0e1b5d731461320c10df0a9c12267e5f0/docs/assets/images/examples/sb2nov.png" width="350"></td>
</tr>
<tr>
<td><img alt="Example CV using the ModernCV theme with a sidebar layout and colored name" src="https://raw.githubusercontent.com/rendercv/rendercv/9b7830a0e1b5d731461320c10df0a9c12267e5f0/docs/assets/images/examples/moderncv.png" width="350"></td>
<td><img alt="Example CV using the Engineering Classic theme with a traditional academic style" src="https://raw.githubusercontent.com/rendercv/rendercv/9b7830a0e1b5d731461320c10df0a9c12267e5f0/docs/assets/images/examples/engineeringclassic.png" width="350"></td>
<td><img alt="Example CV using the Harvard theme with a clean serif font and full-width lines" src="https://raw.githubusercontent.com/rendercv/rendercv/9b7830a0e1b5d731461320c10df0a9c12267e5f0/docs/assets/images/examples/harvard.png" width="350"></td>
</tr>
</table>

See the [examples](examples/) directory for the full source of each.

## Getting Started

```
typst init @preview/rendercv
```

Or import into an existing file:

```typst
#import "@preview/rendercv:0.3.0": *
```

## Usage

```typst
#import "@preview/rendercv:0.3.0": *

#show: rendercv.with(
  name: "John Doe",
)

= John Doe

#headline([Software Engineer])

#connections(
  [San Francisco, CA],
  [#link("mailto:john@example.com")[john\@example.com]],
  [#link("https://github.com/johndoe")[github.com/johndoe]],
)

== Education

#education-entry(
  [*Princeton University*, PhD in Computer Science -- Princeton, NJ],
  [Sept 2018 -- May 2023],
  main-column-second-row: [
    - Thesis: Efficient Neural Architecture Search
    - GPA: 3.97/4.00
  ],
)

== Experience

#regular-entry(
  [*Software Engineer*, Company Name -- City, State],
  [June 2023 -- present],
  main-column-second-row: [
    - Developed and deployed scalable web applications
    - Improved system performance by 40%
  ],
)

== Skills

*Languages:* Python, JavaScript, TypeScript, Rust
```

## Components

- **`headline(content)`** -- Headline below the name
- **`connections(...items)`** -- Contact info with automatic line wrapping
- **`connection-with-icon(icon-name, content)`** -- Connection item with a [Font Awesome](https://fontawesome.com/search?o=r&m=free) icon
- **`regular-entry(main-column, date-and-location-column, main-column-second-row: none)`** -- Standard entry for experience, projects, publications
- **`education-entry(main-column, date-and-location-column, degree-column: none, main-column-second-row: none)`** -- Entry with an optional degree column
- **`summary(content)`** -- Summary line within an entry
- **`content-area(content)`** -- Text content wrapper (applied automatically to sections without entry components)
- **`reversed-numbered-entries(content)`** -- Reverse-numbered list
- **`link(dest, body, icon: none, if-underline: none, if-color: none)`** -- Enhanced link with customizable styling

## Customization

Everything is customizable through `rendercv.with()`. A few examples:

```typst
#show: rendercv.with(
  // Page
  page-size: "a4",
  page-top-margin: 0.7in,
  text-direction: rtl,                    // right-to-left support

  // Colors
  colors-name: rgb(0, 79, 144),
  colors-section-titles: rgb(0, 79, 144),

  // Typography
  typography-font-family-body: "Source Sans 3",
  typography-font-size-body: 10pt,
  typography-alignment: "justified",       // "left", "justified-with-no-hyphenation"
  typography-bold-name: true,

  // Header
  header-alignment: center,
  header-connections-separator: "|",
  header-connections-show-icons: true,

  // Section titles
  section-titles-type: "with_partial_line", // "with_full_line", "without_line", "moderncv", "centered_without_line", "centered_with_partial_line", "centered_with_centered_partial_line", "centered_with_full_line"

  // Entries
  entries-date-and-location-width: 4.15cm,
  entries-highlights-bullet: "■",

  // Links
  links-underline: true,
  links-show-external-link-icon: true,
)
```

For the full list of parameters with defaults, see [`lib.typ`](lib.typ).

Optional font controls are available for `body`, `name`, `headline`, `connections`,
and `section-titles`:

```typst
#show: rendercv.with(
  typography-font-weight-body: 350,
  typography-bold-weight-body: 650,
  typography-letter-spacing-body: 0.05em,
)
```

All three controls default to `none`. A font weight overrides the role's legacy
bold Boolean. A bold weight selects an absolute weight for strong text and for
roles whose bold Boolean is enabled and whose base weight is omitted. Without a
bold weight, strong text keeps its normal relative increase. Letter spacing adds
Typst tracking and keeps font kerning enabled.

`section-titles-space-between-text-and-line` optionally sets the horizontal gap on
each side of a title in either centred partial-line style. Omitting it preserves
the existing `0.3em` gap.

RenderCV's Python renderer prepares temporary static instances for explicitly
selected variable weights when generating PDF and PNG files. Source font files
are unchanged. Real italic or oblique faces and supported `ital`/`slnt` axes remain
available. The Typst package itself does not prepare fonts: compiling an exported
`.typ` file separately requires suitable static fonts or a compiler that supports
the variable font. It also requires this updated bundled library: the published
`@preview/rendercv:0.3.0` package does not include the new arguments.

## RenderCV

This package is part of [RenderCV](https://github.com/rendercv/rendercv), which also offers a CLI tool and a web app at [rendercv.com](https://rendercv.com) -- write your CV in YAML and get a PDF using this same package under the hood.
