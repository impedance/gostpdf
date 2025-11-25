from pathlib import Path


def test_template_has_font_fallbacks() -> None:
    content = Path("templates/gost.tex").read_text(encoding="utf-8")

    assert "\\IfFontExistsTF{$fonts.main$}" in content
    assert "\\IfFontExistsTF{$fonts.mono$}" in content
    assert "Latin Modern Roman" in content
    assert "Latin Modern Mono" in content


def test_template_defines_tightlist() -> None:
    content = Path("templates/gost.tex").read_text(encoding="utf-8")
    assert "\\providecommand{\\tightlist}" in content


def test_template_defines_shaded_environment() -> None:
    content = Path("templates/gost.tex").read_text(encoding="utf-8")
    assert "\\newenvironment{Shaded}" in content


def test_template_defines_highlight_macros() -> None:
    content = Path("templates/gost.tex").read_text(encoding="utf-8")
    assert "\\newcommand{\\AttributeTok}[1]" in content
    assert "\\newcommand{\\KeywordTok}[1]" in content
