from rednotebook.data import Day, Month


def test_compare():
    year_number = 2000
    month_number = 10
    day_number = 15
    month = Month(year_number, month_number)
    day = Day(month, day_number)

    eq_day = Day(month, day_number)
    assert(day == eq_day)

    greater_day = Day(month, day_number + 1)
    assert(day < greater_day)
    assert(day <= greater_day)

    lesser_day = Day(month, day_number - 1)
    assert(day > lesser_day)
    assert(day >= lesser_day)


def test_to_string():
    year_number = 2000
    month_number = 10
    day_number = 15
    month = Month(year_number, month_number)
    day = Day(month, day_number)

    str_version = "{0}-{1}-{2:02d}".format(
        year_number, month_number, day_number)
    assert(str(day) == str_version)


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
