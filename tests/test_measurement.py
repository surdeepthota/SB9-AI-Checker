"""Layer 2: the pure SB 9 threshold arithmetic and the disclosure-detection rules."""

import pytest

from peachcheck.layers.measurement import (
    AI_USE_PATTERN,
    EVENTS_CAVEAT_PATTERN,
    OcrLine,
    _disclosure_block,
    check_audio_parity,
    check_contrast,
    check_text_height,
    check_visible_duration,
    find_disclosure_lines,
    is_disclosure_line,
    normalize_ocr_text,
)


# ---- §21-5-92 format arithmetic ----
def test_text_height_thirty_percent_bar():
    assert check_text_height(300, 1000).passed
    assert not check_text_height(299, 1000).passed
    assert check_text_height(150, 1000).measured_value == 0.15


def test_visible_duration_bar_and_zero_frames():
    assert check_visible_duration(30, 100).passed
    assert not check_visible_duration(29, 100).passed
    assert not check_visible_duration(0, 0).passed  # no frames -> fail, not crash


def test_contrast_black_on_white_hits_safe_harbor():
    result = check_contrast((0, 0, 0), (255, 255, 255), body_text_contrast_ratio=21.0)
    assert result.measured_value == 21.0
    assert result.passed


def test_contrast_bar_is_ads_own_text_when_lower():
    # Ad body text has 5:1 contrast; disclosure at 6:1 passes even though it's far
    # from the safe harbor.
    result = check_contrast((80, 80, 80), (255, 255, 255), body_text_contrast_ratio=5.0)
    assert result.required_bar == 5.0
    assert result.passed


def test_audio_parity_tolerances():
    volume, rate = check_audio_parity(-14.0, -14.5, 150, 152)
    assert volume.passed and rate.passed
    volume, rate = check_audio_parity(-14.0, -20.0, 150, 190)
    assert not volume.passed and not rate.passed


# ---- disclosure-content detection rules ----
@pytest.mark.parametrize(
    "text",
    [
        "This ad was generated with artificial intelligence.",
        "Content created using AI.",
        "AI was used to produce this advertisement.",
        "GENERATED WITH ARTIFICIAL INTELLIGENCE",
    ],
)
def test_ai_use_pattern_matches(text):
    assert AI_USE_PATTERN.search(text)


def test_ai_use_pattern_rejects_plain_political_copy():
    assert not AI_USE_PATTERN.search("Vote for Jane Doe. Paid for by the Doe Committee.")


def test_events_caveat_tolerates_ocr_dropped_spaces():
    # OCR really produces this: "MAY NOTHAVE ACTUALLY OCCURRED_"
    assert EVENTS_CAVEAT_PATTERN.search("may nothave actually occurred_")


def test_normalize_fixes_ai_misread_as_al():
    assert "with AI." in normalize_ocr_text("Generated with Al.")
    # Must not rewrite ordinary words containing "al"
    assert normalize_ocr_text("Alabama values") == "Alabama values"


# ---- disclosure block geometry ----
def _line(text, top, height=40, left=10, width=500):
    return OcrLine(text=text, left=left, top=top, width=width, height=height)


def test_wrapped_phrase_flags_both_lines():
    lines = [
        _line("GENERATED WITH ARTIFICIAL", 100),
        _line("INTELLIGENCE.", 150),
        _line("UNRELATED HEADLINE", 900),
    ]
    found = find_disclosure_lines(lines)
    assert [l.text for l in found] == ["GENERATED WITH ARTIFICIAL", "INTELLIGENCE."]


def test_line_above_a_self_matching_line_is_not_dragged_in():
    # "VOTE NOVEMBER 3" sits directly above the disclosure; joining it with the next
    # line matches (the next line matches alone), but the slogan itself is not
    # disclosure text and must stay out of the measured block.
    lines = [
        _line("VOTE NOVEMBER 3", 100),
        _line("Paid for by the Peach Committee. Generated with AI.", 160),
    ]
    found = find_disclosure_lines(lines)
    assert [l.text for l in found] == ["Paid for by the Peach Committee. Generated with AI."]


def test_sandwiched_line_joins_the_block():
    lines = [
        _line("PAID FOR BY PEACHES FOR", 100),
        _line("GEORGIA COMMITTEE. THIS", 150),  # matches nothing alone
        _line("AD WAS GENERATED WITH AI.", 200),
    ]
    found = find_disclosure_lines(lines)
    assert len(found) == 3


def test_block_union_covers_contiguous_lines_only():
    close = [_line("a", 100, 40), _line("b", 160, 40)]
    far = [_line("c", 900, 40)]
    block = _disclosure_block(close + far)
    # tallest cluster is the two contiguous lines: 100 -> 200
    assert block.top == 100
    assert block.height == 100


def test_is_disclosure_line_includes_sponsor():
    assert is_disclosure_line("Paid for by the Peach Committee")
