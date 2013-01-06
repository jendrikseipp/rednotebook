import datetime
import re

from rednotebook.gui import imports

def test_plaintext_date_regex():
    ref_date = datetime.date(2010, 5, 8)
    for test in ['2010-05-08', '2010.05-08', '2010:05_08.TxT', '20100508.TXT']:
        match = imports.PlainTextImporter.date_exp.match(test)
        date = datetime.date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        assert date == ref_date
