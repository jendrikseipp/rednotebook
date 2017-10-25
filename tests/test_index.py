import datetime

from rednotebook import index


def test_index():
    i = index.Index()
    date1 = datetime.date(2017, 10, 24)
    date2 = datetime.date(2017, 10, 25)
    i.add(date1, {"foo", "bar"})
    assert i._word_to_dates == {"foo": {date1}, "bar": {date1}}
    assert i.find("foo") == {date1}
    i.add(date1, {"foo", "bar"})
    assert i._word_to_dates == {"foo": {date1}, "bar": {date1}}
    assert i.find("foo") == {date1}
    i.add(date2, {"bar", "baz"})
    assert i._word_to_dates == {"foo": {date1}, "bar": {date1, date2}, "baz": {date2}}
    i.remove(date1, {"foo", "bar"})
    assert i._word_to_dates == {"bar": {date2}, "baz": {date2}}
    i.clear()
    assert i._word_to_dates == {}
