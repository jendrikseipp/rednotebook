import re

from rednotebook.data import Day, Month

def test_hashtags():
    month = Month(2000, 10)
    day = Day(month, 20)
    assert day.hashtags == []
    day.text = '#tag'
    assert day.hashtags == ['tag']
    day.text = 'abc #tag'
    assert day.hashtags == ['tag']
    day.text = 'abc #tag_with_longer_name'
    assert day.hashtags == ['tag_with_longer_name']
    day.text = 'abc #tag def'
    assert day.hashtags == ['tag']

