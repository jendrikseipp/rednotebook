import pytest

from datetime import date
from rednotebook.data import Month, Day  # Assuming you have access to these

from rednotebook.journal import Journal

@pytest.fixture
def mock_month():
    month = Month(2024, 10)
    day1 = Day(month, 1, {"text": "Example text", "Aria": {}})
    day2 = Day(month, 2, {"text": "More example text", "Aria": {}, "Opera":{}, "Étude":{}})
    day3 = Day(month, 3, {"text": "Another text", "Sonata": {}, "Prelude": {}, "Opera": {}, "Concerto":{}})

    month.days[1] = day1
    month.days[2] = day2
    month.days[3] = day3
    
    yield month


def test_categories(mock_month):
    # Create an empty journal instance
    journal = Journal()

    # Add a month with no days to the journal
    journal.months = { (2024, 10): Month(2024, 10) }

    # Ensure that the categories list is empty
    assert journal.categories == [], "Expected no categories in an empty journal"

    # Add a month with days to the journal
    journal.months = { (2024, 10): mock_month }

    # Assert the categories property returns expected categories sorted alphabetically
    expected_categories = ['Aria', 'Concerto', 'Étude', 'Opera', 'Prelude', 'Sonata']
    assert journal.categories == expected_categories