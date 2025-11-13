import pytest
from django.template import Context, Template

from apps.common.utils import format_clp


@pytest.mark.parametrize(
    "value, expected",
    [
        (0, "$0"),
        (19990, "$19.990"),
        (19990.4, "$19.990"),
        ("24990", "$24.990"),
        (None, "$0"),
        ("", "$0"),
        ("abc", "$0"),
    ],
)
def test_format_clp(value, expected):
    assert format_clp(value) == expected


def test_template_filter_clp():
    template = Template("{% load currency %}{{ price|clp }}")
    rendered = template.render(Context({"price": 19990}))
    assert rendered == "$19.990"

