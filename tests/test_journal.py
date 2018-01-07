import datetime

import sys
import pytest

# Import patch so that we can remove dependencies
from unittest.mock import patch


from rednotebook import journal
from rednotebook import info


def test_empty_journal():
    """Regression test to find out what is going to happen when we
    open an empty journal.
    This test is not good as we need to work around dependencies
    in existing code.
    """
    # Remove dependency to the main window
    with patch('rednotebook.journal.MainWindow') as mockWindow:
        # Remove dependency to open_journal as it does to many fancy things
        # instead we setup data ourself
        with patch.object(journal.Journal,'open_journal') as mockOpen:

            # Arrange
            header='==Header=='
            today = datetime.date.today()

            myjournal = journal.Journal()
            myjournal.month = None
            myjournal.load_day( today )

            # This is now a mockWindow initalized from the constructor
            myjournal.frame.get_day_text.return_value=header
            # Return some fake data. This is called somewhere in the DUT
            myjournal.frame.categories_tree_view.get_day_content.\
                return_value = {'text': ''}

            # Act: Call the DUT
            myjournal.add_instruction_content()

            # Assert
            myjournal.load_day( today )
            # TODO: Why is the example content not appearing here?
            #assert myjournal.day.content != {'text': header}
