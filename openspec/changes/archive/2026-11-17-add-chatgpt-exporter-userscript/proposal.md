# Add ChatGPT Exporter for Agents

## Problem

The repository lacks a maintained, privacy-first way to export an individual ChatGPT conversation into durable human-readable and agent-ingestion formats. Existing extension workflows may depend on server-side PDF generation, opaque release channels, or DOM-only extraction that becomes incomplete on virtualized conversations.

## Proposed change

Add a ScriptCat-compatible userscript that captures the active conversation branch using a same-origin API path with an explicitly labeled DOM fallback. Provide local Markdown, agent Markdown, JSON, JSONL, gzip JSONL, CSV, text, standalone HTML, clipboard, and print/PDF output.

Publish a stable production installer and updater while retaining a checksum-verified source bundle in this repository.

## Goals

- local export with no telemetry or third-party export service;
- rate-limit-sensitive request behavior;
- deterministic, schema-backed downstream-agent output;
- configurable capture, network, export, chunking, and UI behavior;
- responsive and accessible UI across desktop and mobile layouts;
- reproducible source and validation evidence.

## Non-goals

- account-wide archive export;
- fetching private attachment bytes;
- preserving hidden model reasoning;
- a hosted document-conversion backend;
- guaranteed compatibility with future undocumented ChatGPT response shapes.
