# Localization Checklist

Use this checklist when planning or reviewing i18n work.

## Architecture

- Identify the existing i18n library, catalog format, route strategy, and fallback rules.
- Confirm whether locale is selected by URL, domain, user setting, cookie, browser header, or explicit picker.
- Keep language, region, currency, timezone, and legal market rules as separate concepts unless the product has a documented combined market model.
- Ensure server-rendered, client-rendered, email, docs, API error, and background-job surfaces can receive locale context.

## Message Catalogs

- Extract user-visible strings into stable semantic keys.
- Store whole sentences instead of sentence fragments.
- Use named variables with translator notes.
- Use plural/select variants for count-sensitive or user-type-sensitive text.
- Detect missing keys, unused keys, duplicate keys, and variable mismatch in CI where possible.
- Keep source text changes intentional because they can invalidate translation memory.

## Formatting

- Use locale-aware date, time, timezone, relative-time, number, percent, currency, unit, and list formatting.
- Verify parsing and validation for localized numeric input, phone numbers, addresses, postal codes, and names.
- Test sorting, casing, search, slug generation, and normalization for non-English input.
- Check emails, exports, PDFs, charts, tables, and analytics labels for formatted values.

## Routing And Metadata

- Verify redirects, canonical URLs, alternate links, hreflang, sitemap entries, and Open Graph metadata.
- Ensure locale-prefixed links do not drop state or route params.
- Confirm caches vary on the right locale signal.
- Preserve a deterministic fallback for unsupported locales.

## Layout And Accessibility

- Run pseudo-locale QA for string expansion, clipping, wrapping, interpolation, and hardcoded strings.
- Check RTL layout, icon direction, keyboard order, focus order, and mixed-direction user content where relevant.
- Set language and direction attributes at the document or scoped content boundary.
- Translate aria labels, alt text, live-region messages, validation messages, and error states.

## Translation Handoff

- Provide translator notes, screenshots, character constraints, variable descriptions, and product glossary entries.
- Mark non-translatable product names, command names, code snippets, and placeholders.
- Separate legal, pricing, tax, and regulated content for market review.

## Release Readiness

- Catalog completeness passes for all release locales.
- Missing translations fail visibly in development.
- Production fallback is explicit and monitored.
- Pseudo-locale and representative locale checks pass.
- At least one non-US formatting test passes.
- RTL checks pass for any RTL target or user-generated bidirectional content.
