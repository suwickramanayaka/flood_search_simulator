"""Tests for reusable centered summary-card markup."""

from visualizations.card_renderer import build_centered_card_html


def test_centered_card_html_centers_and_escapes_content() -> None:
    html = build_centered_card_html("Current <node>", "A & B\nReached")

    assert "text-align:center" in html
    assert "align-items:center" in html
    assert "justify-content:center" in html
    assert "margin-bottom:0.75rem" in html
    assert "padding:0.85rem 1rem" in html
    assert "box-sizing:border-box" in html
    assert "Current &lt;node&gt;" in html
    assert "A &amp; B<br>Reached" in html


def test_prominent_card_uses_larger_value_size() -> None:
    regular = build_centered_card_html("Step", 3)
    prominent = build_centered_card_html("Step", 3, prominent=True)

    assert "font-size:1rem" in regular
    assert "font-size:1.85rem" in prominent
