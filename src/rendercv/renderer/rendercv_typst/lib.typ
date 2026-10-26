#import "@preview/fontawesome:0.6.0": fa-icon

// State to hold rendercv configuration for use by components
#let rendercv-config = state("rendercv-config", (:))

// Scope optional font controls to a typography role. In particular, body
// tracking and strong weights must not change the header roles' defaults.
#let font-controls(role, body) = context {
  let config = rendercv-config.get()
  let weight = config.at("typography-font-weight-" + role)
  let bold-weight = config.at("typography-bold-weight-" + role)
  let tracking = config.at("typography-letter-spacing-" + role)
  let is-body = role == "body"
  let body-bold-weight = config.at("typography-bold-weight-body")
  let body-tracking = config.at("typography-letter-spacing-body")

  if weight == none and config.at("typography-bold-" + role, default: false) {
    weight = bold-weight
  }
  set text(weight: weight) if weight != none
  set text(tracking: tracking) if tracking != none
  set text(tracking: config.at("default-letter-spacing")) if (
    not is-body and tracking == none and body-tracking != none
  )

  if bold-weight != none {
    // Replace the strong element's weight increase with an absolute weight.
    // Leaving its native increase in place would add 300 to this selection.
    show strong: it => text(weight: bold-weight, it.body)
    body
  } else if not is-body and body-bold-weight != none {
    // A local rule prevents the body's absolute weight from leaking into a
    // header role. Retain that role's normal relative strong behaviour.
    show strong: it => context {
      let weight = text.weight
      if type(weight) == str {
        weight = (
          thin: 100, extralight: 200, light: 300, regular: 400, medium: 500,
          semibold: 600, bold: 700, extrabold: 800, black: 900,
        ).at(weight)
      }
      text(weight: calc.clamp(weight + it.delta, 100, 900), it.body)
    }
    body
  } else {
    body
  }
}

// Direction-aware inset: maps logical start/end to physical left/right.
// Must be called from within a `context` scope.
#let directional-inset(start: 0cm, end: 0cm) = {
  let is-rtl = rendercv-config.get().at("is-rtl")
  if is-rtl {
    (left: end, right: start)
  } else {
    (left: start, right: end)
  }
}

#let headline(headline) = {
  metadata("skip-content-area")
  context {
    let config = rendercv-config.get()
    let typography-font-size-headline = config.at("typography-font-size-headline")
    let typography-font-family-headline = config.at("typography-font-family-headline")
    let typography-bold-headline = config.at("typography-bold-headline")
    let colors-headline = config.at("colors-headline")
    let typography-small-caps-headline = config.at("typography-small-caps-headline")
    let header-alignment = config.at("header-alignment")
    let header-space-below-headline = config.at("header-space-below-headline")
    set text(
      fill: colors-headline,
      font: typography-font-family-headline,
      size: typography-font-size-headline,
      weight: if typography-bold-headline { 700 } else { 400 },
    )
    set align(header-alignment)
    show: font-controls.with("headline")
    block(
      if typography-small-caps-headline { smallcaps(headline) } else { headline },
      width: 100%,
      height: auto,
    )
    v(header-space-below-headline, weak: true)
  }
}

#let connections(..connections) = {
  metadata("skip-content-area")

  context {
    let config = rendercv-config.get()
    let typography-line-spacing = config.at("typography-line-spacing")
    let header-connections-space-between-connections = config.at("header-connections-space-between-connections")
    let header-connections-separator = config.at("header-connections-separator")
    let page-left-margin = config.at("page-left-margin")
    let page-right-margin = config.at("page-right-margin")
    let header-space-below-connections = config.at("header-space-below-connections")
    let section-titles-space-above = config.at("section-titles-space-above")
    let colors-connections = config.at("colors-connections")
    let typography-font-family-connections = config.at("typography-font-family-connections")
    let typography-font-size-connections = config.at("typography-font-size-connections")
    let typography-small-caps-connections = config.at("typography-small-caps-connections")
    let typography-bold-connections = config.at("typography-bold-connections")
    let header-alignment = config.at("header-alignment")

    set par(spacing: 0pt, leading: typography-line-spacing * 1.7, justify: false)
    set text(
      fill: colors-connections,
      font: typography-font-family-connections,
      size: typography-font-size-connections,
      weight: if typography-bold-connections { 700 } else { 400 },
    )
    show: font-controls.with("connections")

    let separator = (
      h(header-connections-space-between-connections / 2, weak: true)
        + header-connections-separator
        + h(header-connections-space-between-connections / 2, weak: true)
    )
    let separator-width = (
      measure(header-connections-separator).width + header-connections-space-between-connections
    )
    if connections.pos().len() > 0 {
      set align(header-alignment)
      box(
        {
          layout(size => {
            let line-width = 0cm
            for (i, connection) in connections.pos().enumerate() {
              let connection-body = if typography-small-caps-connections { smallcaps(connection) } else { connection }
              let connection-width = measure(connection-body).width
              let is-last = i == connections.pos().len() - 1

              // Check if adding this connection + separator would exceed the line
              if (
                line-width + connection-width + separator-width > size.width and line-width > 0cm
              ) {
                linebreak()
                line-width = 0cm
              }

              // Add separator only if we're not at the start of a line
              if line-width > 0cm {
                separator
              }

              box(connection-body, width: auto)
              line-width = line-width + connection-width + (if line-width > 0cm { separator-width } else { 0cm })
            }
          })
        },
        width: 100%,
        height: auto,
      )
    }
    v(header-space-below-connections - section-titles-space-above)
  }
}

#let original-link = link
#let link(dest, body, icon: none, if-underline: none, if-color: none) = context {
  let config = rendercv-config.get()
  let links-underline = config.at("links-underline")
  let links-show-external-link-icon = config.at("links-show-external-link-icon")
  let typography-font-size-body = config.at("typography-font-size-body")
  let colors-links = config.at("colors-links")

  let icon = icon
  if icon == none {
    if links-show-external-link-icon {
      icon = true
    } else {
      icon = false
    }
  }
  let if-underline = if-underline
  if if-underline == none {
    if links-underline {
      if-underline = true
    } else {
      if-underline = false
    }
  }
  let if-color = if-color
  if if-color == none {
    if-color = true
  }

  let body = [#if if-underline [#underline(body)] else [#body]]
  if icon {
    let ext-icon-content = fa-icon("external-link", size: 0.65em)
    let icon-width = measure(ext-icon-content).width
    // Zero-height box reserves horizontal space but doesn't affect line height
    // or baseline. place() renders the icon out of flow, positioned above the
    // baseline to align visually with text.
    let ext-icon = box(
      width: icon-width,
      height: 0pt,
      baseline: 0pt,
      place(dy: -0.75em, ext-icon-content),
    )
    // Wrap body in box to create BiDi isolation — the box becomes a neutral
    // atomic inline, so the paragraph direction controls the icon's placement.
    body = [#box[#body]#h(typography-font-size-body / 4)#ext-icon]
  }
  body = [#if if-color [#set text(fill: colors-links);#body] else [#body]]
  original-link(dest, body)
}

// Box around body creates BiDi isolation — the icon and body are both neutral
// atomic inlines, so the paragraph direction controls their relative order.
#let connection-with-icon(icon-name, body) = [
  #fa-icon(icon-name, size: 0.9em) #h(0.05cm) #box[#body]
]

#let content-area(content) = context {
  let config = rendercv-config.get()
  let entries-side-space = config.at("entries-side-space")
  let entries-date-and-location-width = config.at("entries-date-and-location-width")
  let entries-space-between-columns = config.at("entries-space-between-columns")
  let entries-allow-page-break = config.at("entries-allow-page-break")
  let sections-space-between-text-based-entries = config.at("sections-space-between-text-based-entries")
  let section-titles-type = config.at("section-titles-type")
  let typography-line-spacing = config.at("typography-line-spacing")
  let justify = config.at("justify")
  let entries-highlights-bullet = config.at("entries-highlights-bullet")
  let entries-highlights-nested-bullet = config.at("entries-highlights-nested-bullet")
  let entries-highlights-space-between-bullet-and-text = config.at(
    "entries-highlights-space-between-bullet-and-text",
  )
  let start-align = config.at("start-align")

  let start-space = entries-side-space
  if section-titles-type == "moderncv" {
    start-space = (
      start-space + entries-date-and-location-width + entries-space-between-columns
    )
  }

  set par(
    spacing: sections-space-between-text-based-entries + typography-line-spacing,
    leading: typography-line-spacing,
    justify: justify,
  )
  set align(start-align)
  set enum(
    spacing: sections-space-between-text-based-entries + typography-line-spacing,
  )
  set list(
    marker: (entries-highlights-bullet, entries-highlights-nested-bullet),
    indent: 0cm,
    spacing: sections-space-between-text-based-entries + typography-line-spacing,
    body-indent: entries-highlights-space-between-bullet-and-text,
  )

  block(
    content,
    breakable: entries-allow-page-break,
    below: sections-space-between-text-based-entries + typography-line-spacing,
    inset: directional-inset(start: start-space, end: entries-side-space),
    width: 100%,
  )
}

#let summary(summary) = {
  context {
    let config = rendercv-config.get()
    let entries-summary-space-left = config.at("entries-summary-space-left")
    let entries-summary-space-above = config.at("entries-summary-space-above")
    let typography-line-spacing = config.at("typography-line-spacing")
    block(
      summary,
      inset: directional-inset(start: entries-summary-space-left),
      above: entries-summary-space-above + typography-line-spacing,
    )
  }
}

#let regular-entry(main-column, date-and-location-column, main-column-second-row: none) = {
  metadata("skip-content-area")

  context {
    let config = rendercv-config.get()
    let section-titles-type = config.at("section-titles-type")
    let entries-date-and-location-width = config.at("entries-date-and-location-width")
    let entries-space-between-columns = config.at("entries-space-between-columns")
    let entries-highlights-bullet = config.at("entries-highlights-bullet")
    let entries-highlights-nested-bullet = config.at("entries-highlights-nested-bullet")
    let entries-highlights-space-between-items = config.at(
      "entries-highlights-space-between-items",
    )
    let entries-highlights-space-between-bullet-and-text = config.at(
      "entries-highlights-space-between-bullet-and-text",
    )
    let entries-highlights-space-above = config.at("entries-highlights-space-above")
    let typography-line-spacing = config.at("typography-line-spacing")
    let entries-allow-page-break = config.at("entries-allow-page-break")
    let sections-space-between-regular-entries = config.at("sections-space-between-regular-entries")
    let entries-side-space = config.at("entries-side-space")
    let justify = config.at("justify")
    let typography-date-and-location-column-alignment = config.at("typography-date-and-location-column-alignment")
    let entries-highlights-space-left = config.at("entries-highlights-space-left")
    let start-align = config.at("start-align")

    set list(
      marker: (entries-highlights-bullet, entries-highlights-nested-bullet),
      indent: entries-highlights-space-left,
      spacing: entries-highlights-space-between-items + typography-line-spacing,
      body-indent: entries-highlights-space-between-bullet-and-text,
    )
    let list-depth = state("list-depth", 0)
    show list.item: i => {
      list-depth.update(d => d + 1)
      i
      list-depth.update(d => d - 1)
    }
    show list: l => {
      context if list-depth.get() == 1 {
        v(entries-highlights-space-above)
      }
      context if list-depth.get() == 2 {
        v(entries-highlights-space-between-items)
      }
      l
    }
    set par(
      spacing: typography-line-spacing,
      leading: typography-line-spacing,
      justify: justify,
    )
    block(
      {
        if section-titles-type == "moderncv" {
          grid(
            columns: (entries-date-and-location-width, 1fr),
            column-gutter: entries-space-between-columns,
            align: (typography-date-and-location-column-alignment, start-align),
            [
              #date-and-location-column
            ],
            [
              #main-column

              #main-column-second-row
            ],
          )
        } else {
          if repr(main-column) != "[ ]" or repr(date-and-location-column) != "[ ]" {
            grid(
              columns: (1fr, entries-date-and-location-width),
              column-gutter: entries-space-between-columns,
              align: (start-align, typography-date-and-location-column-alignment),
              main-column, date-and-location-column,
            )
          }
          set align(start-align)
          main-column-second-row
        }
      },
      breakable: entries-allow-page-break,
      below: sections-space-between-regular-entries + typography-line-spacing,
      inset: (
        left: entries-side-space,
        right: entries-side-space,
      ),
      width: 100%,
    )
  }
}

#let education-entry(main-column, date-and-location-column, degree-column: none, main-column-second-row: none) = {
  metadata("skip-content-area")

  context {
    let config = rendercv-config.get()
    let entries-space-between-columns = config.at("entries-space-between-columns")
    let entries-degree-width = config.at("entries-degree-width")
    let start-align = config.at("start-align")

    regular-entry(
      if degree-column != none {
        grid(
          columns: (entries-degree-width, 1fr),
          column-gutter: entries-space-between-columns,
          align: (start-align, auto),
          [
            #degree-column
          ],
          [
            #main-column
          ],
        )
      } else {
        main-column
      },
      date-and-location-column,
      main-column-second-row: if main-column-second-row != none and repr(main-column-second-row) != "[ ]" {
        [
          #block(
            main-column-second-row,
            inset: directional-inset(
              start: if degree-column != none { entries-degree-width + entries-space-between-columns } else { 0cm },
            ),
          )
        ]
      } else { none },
    )
  }
}

#let reversed-numbered-entries(entries) = {
  set enum(reversed: true)
  entries
}

#let rendercv(
  doc,
  name: "John Doe",
  title: "John Doe's CV",
  footer: context { "Page " + str(here().page()) + " of " + str(counter(page).final().first()) + "" },
  top-note: "Last updated in " + datetime.today().display(),
  locale-catalog-language: "en",
  text-direction: ltr,
  page-size: "us-letter",
  page-top-margin: 0.7in,
  page-bottom-margin: 0.7in,
  page-left-margin: 0.7in,
  page-right-margin: 0.7in,
  page-show-footer: true,
  page-show-top-note: true,
  colors-body: rgb(0, 0, 0),
  colors-name: rgb(0, 79, 144),
  colors-headline: rgb(0, 79, 144),
  colors-connections: rgb(0, 79, 144),
  colors-section-titles: rgb(0, 79, 144),
  colors-links: rgb(0, 79, 144),
  colors-footer: rgb(128, 128, 128),
  colors-top-note: rgb(128, 128, 128),
  typography-line-spacing: 0.6em,
  typography-alignment: "justified",
  typography-date-and-location-column-alignment: right,
  typography-font-family-body: "Raleway",
  typography-font-family-name: "Raleway",
  typography-font-family-headline: "Raleway",
  typography-font-family-connections: "Raleway",
  typography-font-family-section-titles: "Raleway",
  typography-font-weight-body: none,
  typography-font-weight-name: none,
  typography-font-weight-headline: none,
  typography-font-weight-connections: none,
  typography-font-weight-section-titles: none,
  typography-bold-weight-body: none,
  typography-bold-weight-name: none,
  typography-bold-weight-headline: none,
  typography-bold-weight-connections: none,
  typography-bold-weight-section-titles: none,
  typography-letter-spacing-body: none,
  typography-letter-spacing-name: none,
  typography-letter-spacing-headline: none,
  typography-letter-spacing-connections: none,
  typography-letter-spacing-section-titles: none,
  typography-font-size-body: 10pt,
  typography-font-size-name: 30pt,
  typography-font-size-headline: 10pt,
  typography-font-size-connections: 10pt,
  typography-font-size-section-titles: 1.4em,
  typography-small-caps-name: false,
  typography-small-caps-headline: false,
  typography-small-caps-connections: false,
  typography-small-caps-section-titles: false,
  typography-bold-name: false,
  typography-bold-headline: false,
  typography-bold-connections: false,
  typography-bold-section-titles: false,
  links-underline: false,
  links-show-external-link-icon: false,
  header-alignment: left,
  header-photo-width: 3.5cm,
  header-space-below-name: 0.7cm,
  header-space-below-headline: 0.7cm,
  header-space-below-connections: 0.7cm,
  header-connections-hyperlink: true,
  header-connections-show-icons: true,
  header-connections-display-urls-instead-of-usernames: false,
  header-connections-separator: "",
  header-connections-space-between-connections: 0.5cm,
  section-titles-type: "with_full_line",
  section-titles-line-thickness: 0.5pt,
  section-titles-space-between-text-and-line: none,
  section-titles-space-above: 0.5cm,
  section-titles-space-below: 0.3cm,
  sections-allow-page-break: true,
  sections-space-between-text-based-entries: 0.3em,
  sections-space-between-regular-entries: 1.2em,
  entries-date-and-location-width: 4.15cm,
  entries-side-space: 0.2cm,
  entries-space-between-columns: 0.1cm,
  entries-allow-page-break: false,
  entries-short-second-row: false,
  entries-degree-width: 1cm,
  entries-summary-space-left: 0cm,
  entries-summary-space-above: 0.12cm,
  entries-highlights-bullet: "•",
  entries-highlights-nested-bullet: "•",
  entries-highlights-space-left: 0cm,
  entries-highlights-space-above: 0.12cm,
  entries-highlights-space-between-items: 0.12cm,
  entries-highlights-space-between-bullet-and-text: 0.5em,
  date: datetime(
    year: 2025,
    month: 12,
    day: 5,
  ),
) = [
  #let (justify, hyphenate) = (
    "justified": (true, true),
    "left": (false, false),
    "justified-with-no-hyphenation": (true, false),
  ).at(typography-alignment)

  #let is-rtl = text-direction == rtl
  #let start-align = if is-rtl { right } else { left }
  #let end-align = if is-rtl { left } else { right }

  // Initialize state with all configuration parameters
  #context rendercv-config.update((
    default-letter-spacing: text.tracking,
    // Direction
    text-direction: text-direction,
    is-rtl: is-rtl,
    start-align: start-align,
    // Page
    page-left-margin: page-left-margin,
    page-right-margin: page-right-margin,
    // Colors
    colors-body: colors-body,
    colors-name: colors-name,
    colors-headline: colors-headline,
    colors-connections: colors-connections,
    colors-section-titles: colors-section-titles,
    colors-links: colors-links,
    colors-footer: colors-footer,
    colors-top-note: colors-top-note,
    // Typography
    typography-line-spacing: typography-line-spacing,
    typography-alignment: typography-alignment,
    typography-date-and-location-column-alignment: typography-date-and-location-column-alignment,
    typography-font-family-body: typography-font-family-body,
    typography-font-family-name: typography-font-family-name,
    typography-font-family-headline: typography-font-family-headline,
    typography-font-family-connections: typography-font-family-connections,
    typography-font-family-section-titles: typography-font-family-section-titles,
    typography-font-weight-body: typography-font-weight-body,
    typography-font-weight-name: typography-font-weight-name,
    typography-font-weight-headline: typography-font-weight-headline,
    typography-font-weight-connections: typography-font-weight-connections,
    typography-font-weight-section-titles: typography-font-weight-section-titles,
    typography-bold-weight-body: typography-bold-weight-body,
    typography-bold-weight-name: typography-bold-weight-name,
    typography-bold-weight-headline: typography-bold-weight-headline,
    typography-bold-weight-connections: typography-bold-weight-connections,
    typography-bold-weight-section-titles: typography-bold-weight-section-titles,
    typography-letter-spacing-body: typography-letter-spacing-body,
    typography-letter-spacing-name: typography-letter-spacing-name,
    typography-letter-spacing-headline: typography-letter-spacing-headline,
    typography-letter-spacing-connections: typography-letter-spacing-connections,
    typography-letter-spacing-section-titles: typography-letter-spacing-section-titles,
    typography-font-size-body: typography-font-size-body,
    typography-font-size-name: typography-font-size-name,
    typography-font-size-headline: typography-font-size-headline,
    typography-font-size-connections: typography-font-size-connections,
    typography-font-size-section-titles: typography-font-size-section-titles,
    typography-small-caps-name: typography-small-caps-name,
    typography-small-caps-headline: typography-small-caps-headline,
    typography-small-caps-connections: typography-small-caps-connections,
    typography-small-caps-section-titles: typography-small-caps-section-titles,
    typography-bold-name: typography-bold-name,
    typography-bold-headline: typography-bold-headline,
    typography-bold-connections: typography-bold-connections,
    typography-bold-section-titles: typography-bold-section-titles,
    // Links
    links-underline: links-underline,
    links-show-external-link-icon: links-show-external-link-icon,
    // Header
    header-alignment: header-alignment,
    header-photo-width: header-photo-width,
    header-space-below-name: header-space-below-name,
    header-space-below-headline: header-space-below-headline,
    header-space-below-connections: header-space-below-connections,
    header-connections-hyperlink: header-connections-hyperlink,
    header-connections-show-icons: header-connections-show-icons,
    header-connections-display-urls-instead-of-usernames: header-connections-display-urls-instead-of-usernames,
    header-connections-separator: header-connections-separator,
    header-connections-space-between-connections: header-connections-space-between-connections,
    // Section titles
    section-titles-type: section-titles-type,
    section-titles-line-thickness: section-titles-line-thickness,
    section-titles-space-above: section-titles-space-above,
    section-titles-space-below: section-titles-space-below,
    // Sections
    sections-allow-page-break: sections-allow-page-break,
    sections-space-between-regular-entries: sections-space-between-regular-entries,
    sections-space-between-text-based-entries: sections-space-between-text-based-entries,
    // Entries
    entries-date-and-location-width: entries-date-and-location-width,
    entries-side-space: entries-side-space,
    entries-space-between-columns: entries-space-between-columns,
    entries-allow-page-break: entries-allow-page-break,
    entries-summary-space-left: entries-summary-space-left,
    entries-summary-space-above: entries-summary-space-above,
    entries-highlights-bullet: entries-highlights-bullet,
    entries-highlights-nested-bullet: entries-highlights-nested-bullet,
    entries-highlights-space-left: entries-highlights-space-left,
    entries-highlights-space-above: entries-highlights-space-above,
    entries-highlights-space-between-items: entries-highlights-space-between-items,
    entries-highlights-space-between-bullet-and-text: entries-highlights-space-between-bullet-and-text,
    entries-degree-width: entries-degree-width,
    // Internal computed values
    justify: justify,
  ))

  // Metadata:
  #set document(author: name, title: title, date: date)

  // Page:
  #set page(
    margin: (
      top: page-top-margin,
      bottom: page-bottom-margin,
      left: page-left-margin,
      right: page-right-margin,
    ),
    paper: page-size,
    footer: if page-show-footer and footer != none and footer != "" {
      text(
        fill: colors-footer,
        align(center, [#footer]),
        size: 0.9em,
      )
    } else {
      none
    },
    footer-descent: 0% - 0.6em + page-bottom-margin / 2,
  )

  // Text:
  #set text(
    font: typography-font-family-body,
    size: typography-font-size-body,
    lang: locale-catalog-language,
    dir: text-direction,
    hyphenate: hyphenate,
    fill: colors-body,
    // Disable ligatures for better ATS compatibility:
    ligatures: true,
  )
  #show: font-controls.with("body")

  // Main heading (name):
  #show heading.where(level: 1): it => [
    #set par(spacing: 0pt)
    #set align(header-alignment)
    #set text(
      font: typography-font-family-name,
      size: typography-font-size-name,
      fill: colors-name,
      weight: if typography-bold-name { 700 } else { 400 },
    )
    #show: font-controls.with("name")
    #let body
    #if typography-small-caps-name {
      body = [#smallcaps(it.body)]
    } else {
      body = [#it.body]
    }
    #body
    // Vertical space after the name
    #v(header-space-below-name, weak: true)
  ]

  // Section titles:
  #show heading.where(level: 2): it => [
    #let is-centered = section-titles-type in ("centered_without_line", "centered_with_partial_line", "centered_with_centered_partial_line", "centered_with_full_line")
    #set align(if is-centered { center } else { start-align })
    #set text(size: (1em / 1.2)) // reset
    #set text(
      font: typography-font-family-section-titles,
      size: (typography-font-size-section-titles),
      weight: if typography-bold-section-titles { 700 } else { 400 },
      fill: colors-section-titles,
    )
    #show: font-controls.with("section-titles")
    #let section-title = (
      if typography-small-caps-section-titles [
        #smallcaps(it.body)
      ] else [
        #it.body
      ]
    )
    // Vertical space above the section title
    #v(section-titles-space-above, weak: true)

    #block(
      breakable: false,
      width: 100%,
      [
        #if section-titles-type == "moderncv" [
          #grid(
            columns: (entries-date-and-location-width + entries-side-space, 1fr),
            column-gutter: entries-space-between-columns,
            align: (end-align, start-align),
            [
              #align(horizon, box(
                width: 1fr,
                height: section-titles-line-thickness,
                fill: colors-section-titles,
              ))
            ],
            [
              #section-title
            ],
          )
        ] else if section-titles-type == "centered_without_line" [
          #section-title
        ] else if section-titles-type == "centered_with_partial_line" [
          #grid(
            columns: (1fr, auto, 1fr),
            align: (bottom, center + bottom, bottom),
            column-gutter: if section-titles-space-between-text-and-line != none {
              section-titles-space-between-text-and-line
            } else { 0.3em },
            [#box(width: 1fr, height: section-titles-line-thickness, fill: colors-section-titles)],
            [#section-title],
            [#box(width: 1fr, height: section-titles-line-thickness, fill: colors-section-titles)],
          )
        ] else if section-titles-type == "centered_with_centered_partial_line" [
          #grid(
            columns: (1fr, auto, 1fr),
            align: (horizon, center, horizon),
            column-gutter: if section-titles-space-between-text-and-line != none {
              section-titles-space-between-text-and-line
            } else { 0.3em },
            [#box(width: 1fr, height: section-titles-line-thickness, fill: colors-section-titles)],
            [#section-title],
            [#box(width: 1fr, height: section-titles-line-thickness, fill: colors-section-titles)],
          )
        ] else if section-titles-type == "centered_with_full_line" [
          #section-title
          #v(typography-font-size-body * 0.3)
          #box(width: 1fr, height: section-titles-line-thickness, fill: colors-section-titles)
        ] else [
          #section-title
          #if section-titles-type == "with_partial_line" [
            #box(width: 1fr, height: section-titles-line-thickness, fill: colors-section-titles)
          ] else if section-titles-type == "with_full_line" [

            #v(typography-font-size-body * 0.3)
            #box(width: 1fr, height: section-titles-line-thickness, fill: colors-section-titles)
          ]
        ]
      ],
    )

    // Vertical space after the section title
    #v(section-titles-space-below - 0.5em)
  ]

  // Top note:
  #if page-show-top-note and top-note != none and top-note != "" {
    let dx = if is-rtl { entries-side-space } else { -entries-side-space }
    place(
      top + end-align,
      dy: -page-top-margin / 2,
      dx: dx,
      text(
        [#top-note],
        fill: colors-top-note,
        size: 0.9em,
      ),
    )
  }

  // From: https://github.com/typst/typst/issues/2666
  #let group-sections(content) = {
    let sections = ()
    let preamble = () // Content before any heading

    for element in content.children {
      if element.func() == heading {
        // Push a new section
        sections.push((element, ()))
      } else if sections.len() > 0 {
        // Add to current section
        sections.last().at(1).push(element)
      } else {
        // No heading yet - this is preamble content
        preamble.push(element)
      }
    }

    // Join the content in each section
    let result = sections.map(it => {
      let (title, content) = it
      (title, content.join())
    })

    // Return both preamble and sections
    (preamble: preamble.join(), sections: result)
  }

  #set par(spacing: 0cm)

  #let grouped = group-sections(doc)

  // Render preamble content (before any heading)
  #if grouped.preamble != none and grouped.preamble.func() != parbreak [
    #block(breakable: sections-allow-page-break)[
      #grouped.preamble
    ]
  ]

  // Render sections as before
  #for (section-title, section-content) in grouped.sections [
    #section-title
    #let should-skip = {
      let skip = false
      if section-content != none and section-content.has("children") {
        for child in section-content.children {
          if child.func() == metadata and child.value == "skip-content-area" {
            skip = true
            break
          }
        }
      }
      skip
    }
    #if section-content != none and section-content.func() != parbreak [
      #block(breakable: sections-allow-page-break)[
        #if should-skip [
          #section-content
        ] else [
          #content-area(section-content)
        ]
      ]
    ]
  ]
]
