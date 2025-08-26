import pytest
from unittest.mock import patch, MagicMock
import sys
import itertools

from rednotebook.data import Day, Month
from rednotebook.util import utils


@pytest.fixture
def mock_month():
    month = Month(2024, 10)
    day1 = Day(month, 1, {"text": "Example text", "Aria": {}})
    day2 = Day(
        month, 2, {"text": "More example text", "Aria": {}, "Opera": {}, "Étude": {}}
    )
    day3 = Day(
        month,
        3,
        {
            "text": "Another text",
            "Sonata": {},
            "Prelude": {},
            "Opera": {},
            "Concerto": {},
        },
    )
    day4 = Day(
        month, 4, {"text": "Regression test for issue 778", "Opera": {}, "المُوَشَّح": {}}
    )

    month.days[1] = day1
    month.days[2] = day2
    month.days[3] = day3
    month.days[4] = day4

    yield month


def test_categories(mock_month):
    """Test category extraction from month data structures."""
    # Test empty month has no categories
    empty_month = Month(2024, 10)
    days = [day for day in empty_month.days.values() if not day.empty]
    
    categories = sorted(
        set(itertools.chain.from_iterable(day.categories for day in days)),
        key=utils.safe_strxfrm,
    )
    assert categories == [], "Expected no categories in an empty month"

    # Test month with days has expected categories
    days = [day for day in mock_month.days.values() if not day.empty]
    
    categories = sorted(
        set(itertools.chain.from_iterable(day.categories for day in days)),
        key=utils.safe_strxfrm,
    )

    # Assert the categories are sorted alphabetically using safe_strxfrm
    # The expected order should match what safe_strxfrm produces
    expected_categories = [
        "Aria",
        "Concerto",
        "Opera",
        "Prelude",
        "Sonata",
        "Étude",
        "المُوَشَّح",
    ]

    assert categories == expected_categories
