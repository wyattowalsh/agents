---
skill: playwright-best-practices
source_type: curated-external
researched_at: '2026-06-16T08:46:52Z'
research_tier: standard
mean_confidence: 0.75
---

## Purpose

playwright-best-practices is a comprehensive reference for writing, debugging, and maintaining Playwright tests (E2E, component, API, visual, accessibility, security). It organizes guidance by activity (writing new tests, debugging flaky tests, mobile, auth, file ops, CI/CD, POM vs fixtures, framework-specific, etc.) and points to a large set of reference files (core/, testing-patterns/, debugging/, infrastructure-ci-cd/, etc.). From currents-dev.

## Harness Coverage

Target agents from its dedicated install. Complements general testing and browser-automation patterns.

## Trust And Risks

install-now-after-trust-gate / curated-trust-gated. MIT community skill focused on test patterns rather than privileged execution. Risk surface is the generated test code (flaky tests, CI time, selector fragility) and any browser automation side effects in the SUT. Encourages POM, fixtures, proper waiting, and isolation.

## Install Prerequisites

`npx skills add currents-dev/playwright-best-practices-skill --skill playwright-best-practices -y -g -a ...`

Assumes Playwright is installed in the project; complements the official Playwright CLI skill.

## Upstream Maintainer

currents-dev (https://github.com/currents-dev/playwright-best-practices-skill).

## Comparable Alternatives

Official Playwright docs + examples; other E2E framework skills (Cypress, Selenium, Puppeteer patterns).

> Evidence gathered from public GitHub (raw SKILL.md). Not an endorsement or authority.
