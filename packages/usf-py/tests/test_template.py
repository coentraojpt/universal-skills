import pytest

from usf.template import TemplateError, find_variables, render


def test_plain_variable():
    assert render("Hello {{name}}", {"name": "Ada"}) == "Hello Ada"


def test_default_used_when_missing():
    assert render('X={{v | default("fallback")}}', {}) == "X=fallback"


def test_default_skipped_when_present():
    assert render('X={{v | default("fallback")}}', {"v": "real"}) == "X=real"


def test_default_used_when_empty_string():
    assert render('X={{v | default("fb")}}', {"v": ""}) == "X=fb"


def test_missing_required_raises():
    with pytest.raises(TemplateError):
        render("{{name}}", {})


def test_escape_literal_double_braces():
    assert render("code {{{{literal}}}}", {}) == "code {{literal}}"


def test_find_variables():
    assert find_variables("{{a}} and {{b | default(\"x\")}}") == {"a", "b"}


def test_multiple_same_variable():
    assert render("{{x}} / {{x}}", {"x": "Y"}) == "Y / Y"


def test_invalid_expression_raises():
    with pytest.raises(TemplateError):
        render("{{1bad}}", {"1bad": "x"})
