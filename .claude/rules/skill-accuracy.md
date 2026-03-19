---
paths:
  - "skills/**/SKILL.md"
  - "skills/**/references/*.md"
---

When documenting skills, verify accuracy against actual implementation:

**Type Inventory**: Read classifier prompts, keyword fallbacks, and DB enum definitions before documenting enum values or category lists. Types that exist only in documentation but not in code are **phantom types** — they cause silent failures.

**Encryption/Security Claims**: Verify against actual cryptography library calls (e.g., "AES-256" claimed but Fernet/AES-128-CBC used). Read imports, not comments.

**LLM Classifier Documentation**: Document all four of:
1. **Model** — exact model identifier
2. **Fallback mode** — behavior when API key missing or call fails
3. **Confidence threshold** — minimum score to act on a result
4. **Failure handling** — how to handle classification failures
