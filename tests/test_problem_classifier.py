"""Tests for skills/reasoning-router/scripts/problem-classifier.py."""

import importlib.util
from pathlib import Path

import pytest

# Import the classifier — filename uses a hyphen so importlib is required
_spec = importlib.util.spec_from_file_location(
    "problem_classifier",
    Path(__file__).resolve().parents[1] / "skills" / "reasoning-router" / "scripts" / "problem-classifier.py",
)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

classify = _mod.classify
_classify_complexity = _mod._classify_complexity
_first_sentence = _mod._first_sentence
_normalize_confidence = _mod._normalize_confidence


# ---------------------------------------------------------------------------
# Word-count boundary tests
# ---------------------------------------------------------------------------


class TestWordCountBoundaries:
    """Verify complexity classification at word-count thresholds."""

    @pytest.mark.parametrize(
        ("word_count", "expected"),
        [
            (24, "simple"),
            (25, "moderate"),
            (99, "moderate"),
            (100, "complex"),
        ],
    )
    def test_word_count_thresholds(self, word_count: int, expected: str) -> None:
        text = " ".join(["word"] * word_count)
        level, _, _ = _classify_complexity(text, word_count)
        assert level == expected

    def test_long_input_without_wicked_keywords_stays_complex(self) -> None:
        """A 350-word input without wicked keywords should be 'complex', not 'wicked'."""
        text = " ".join(["word"] * 350)
        level, _, _ = _classify_complexity(text, 350)
        assert level == "complex"

    def test_wicked_requires_keywords(self) -> None:
        """Only wicked keywords can promote to 'wicked'."""
        text = "this problem has no clear solution and is contested by many"
        word_count = len(text.split())
        level, _, signals = _classify_complexity(text, word_count)
        assert level == "wicked"
        assert any(s in signals for s in ["no clear solution", "contested"])


# ---------------------------------------------------------------------------
# Efficiency override tests
# ---------------------------------------------------------------------------


class TestEfficiencyOverride:
    """Verify Tier 1 downgrade for simple problems."""

    def test_simple_input_has_efficiency_override(self) -> None:
        result = classify("quick question")
        assert result["efficiency_override"] is not None

    def test_simple_override_is_tier1_method(self) -> None:
        result = classify("quick question")
        override = result["efficiency_override"]
        assert override is not None
        assert override["method"] in ("aot-light", "sequential-thinking")

    def test_non_simple_has_no_override(self) -> None:
        result = classify(
            "Design a scalable microservice architecture with several "
            "requirements and multiple trade-offs to consider carefully"
        )
        assert result["efficiency_override"] is None

    def test_creative_simple_routes_to_aot_light(self) -> None:
        """Creative+simple should use aot-light, not sequential-thinking (anti-pattern)."""
        result = classify("brainstorm quick ideas")
        override = result["efficiency_override"]
        assert override is not None
        assert override["method"] == "aot-light"


# ---------------------------------------------------------------------------
# Wicked fallback tests
# ---------------------------------------------------------------------------


class TestWickedFallback:
    """Verify per-structure wicked fallback (not blanket string)."""

    def test_wicked_fallback_is_valid_method(self) -> None:
        """Wicked fallback should be a clean method name, not 'creative → cascade'."""
        text = (
            "This problem has no clear solution and involves fundamental disagreement "
            "about values. We need to break down the components separately."
        )
        result = classify(text)
        if result["complexity"]["value"] == "wicked":
            assert "→" not in result["suggested_fallback"]


# ---------------------------------------------------------------------------
# _normalize_confidence edge cases
# ---------------------------------------------------------------------------


class TestNormalizeConfidence:
    """Verify the zero-total guard prevents ZeroDivisionError."""

    def test_zero_total_returns_zero(self) -> None:
        scored = {"a": (0.0, []), "b": (0.0, []), "c": (0.0, [])}
        assert _normalize_confidence(scored, "a") == 0.0

    def test_nonzero_returns_ratio(self) -> None:
        scored = {"a": (3.0, ["x"]), "b": (1.0, ["y"])}
        conf = _normalize_confidence(scored, "a")
        assert conf == 0.75


# ---------------------------------------------------------------------------
# Structure signal scoring
# ---------------------------------------------------------------------------


class TestStructureSignals:
    """Verify structure classification for representative inputs."""

    @pytest.mark.parametrize(
        ("text", "expected_structure"),
        [
            ("break down the components into parts", "decomposable"),
            ("walk through this step by step process", "sequential"),
            ("explore options and compare alternatives", "branching"),
            ("why did the test fail and what caused it", "investigative"),
            ("brainstorm novel approaches to reframe this", "creative"),
            ("this paradox seems both true and contradictory", "contradictory"),
            ("given that we must satisfy these constraints", "constrained"),
            ("the dependencies in this complex system are coupled", "interconnected"),
        ],
    )
    def test_structure_classification(self, text: str, expected_structure: str) -> None:
        result = classify(text)
        assert result["structure"]["value"] == expected_structure


# ---------------------------------------------------------------------------
# Cross-contamination regression
# ---------------------------------------------------------------------------


class TestCrossContamination:
    """Verify 'trace through' routes to sequential, not investigative."""

    def test_trace_through_is_sequential(self) -> None:
        result = classify("trace through the execution step by step")
        assert result["structure"]["value"] == "sequential"

    def test_trace_back_is_investigative(self) -> None:
        result = classify("trace back to the root cause of why this debug failed")
        assert result["structure"]["value"] == "investigative"


# ---------------------------------------------------------------------------
# Domain axis fallback
# ---------------------------------------------------------------------------


class TestDomainFallback:
    """Verify domain influences routing when structure confidence is low."""

    def test_no_structure_signals_defaults_sequential(self) -> None:
        """Input with no structure signals defaults to sequential."""
        result = classify("xyzzy")
        assert result["structure"]["value"] == "sequential"
        assert result["structure"]["confidence"] == 0.1

    def test_unknown_domain_default(self) -> None:
        """Input with no domain signals defaults to 'unknown', not 'engineering'."""
        result = classify("xyzzy")
        assert result["domain"]["value"] == "unknown"


# ---------------------------------------------------------------------------
# signals_found key
# ---------------------------------------------------------------------------


class TestSignalsFound:
    """Verify the top-level signals_found key exists and aggregates all axes."""

    def test_signals_found_key_present(self) -> None:
        result = classify("break down the architecture step by step")
        assert "signals_found" in result

    def test_signals_found_aggregates_axes(self) -> None:
        result = classify("break down the architecture step by step")
        signals = result["signals_found"]
        assert isinstance(signals, list)
        assert len(signals) > 0


# ---------------------------------------------------------------------------
# _first_sentence abbreviation handling
# ---------------------------------------------------------------------------


class TestFirstSentence:
    """Verify _first_sentence doesn't split on abbreviation periods."""

    def test_abbreviation_not_split(self) -> None:
        text = "e.g. explore options for the design"
        sent = _first_sentence(text)
        assert len(sent) > 5  # Should NOT truncate at "e.g."

    def test_question_mark_splits(self) -> None:
        text = "What should we do? Then plan the next steps."
        sent = _first_sentence(text)
        assert sent == "What should we do?"

    def test_exclamation_splits(self) -> None:
        text = "This is broken! We need to fix it."
        sent = _first_sentence(text)
        assert sent == "This is broken!"

    def test_real_sentence_boundary(self) -> None:
        text = "The system is failing. We need to investigate why."
        sent = _first_sentence(text)
        assert sent == "The system is failing."

    def test_no_boundary_returns_full_text(self) -> None:
        text = "no punctuation here"
        sent = _first_sentence(text)
        assert sent == text


# ---------------------------------------------------------------------------
# Complexity confidence ceiling
# ---------------------------------------------------------------------------


class TestComplexityConfidence:
    """Verify complexity confidence can exceed the old 0.80 cap."""

    def test_high_signal_density_exceeds_080(self) -> None:
        """With 5+ matching signals and agreement, confidence should exceed 0.80."""
        text = (
            "many numerous uncertain ambiguous cross-domain interdisciplinary "
            "simultaneously concurrent interacting cascading compliance"
        )
        word_count = len(text.split())
        _, confidence, signals = _classify_complexity(text, word_count)
        assert len(signals) >= 5
        assert confidence > 0.80


# ---------------------------------------------------------------------------
# Output schema completeness
# ---------------------------------------------------------------------------


class TestOutputSchema:
    """Verify the output dict has all required keys."""

    def test_all_required_keys_present(self) -> None:
        result = classify("test input")
        required_keys = {
            "structure",
            "complexity",
            "domain",
            "suggested_method",
            "suggested_fallback",
            "token_tier",
            "efficiency_override",
            "signals_found",
        }
        assert required_keys.issubset(result.keys())

    def test_axis_objects_have_required_subkeys(self) -> None:
        result = classify("test input")
        for axis in ("structure", "complexity", "domain"):
            assert "value" in result[axis]
            assert "confidence" in result[axis]
            assert "signals" in result[axis]
