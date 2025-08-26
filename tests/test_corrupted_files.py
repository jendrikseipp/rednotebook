"""
Tests for handling corrupted journal files.

This module tests that RedNotebook handles corrupted journal files gracefully
by renaming them and continuing to load other files instead of crashing.
"""

import os
import tempfile

from rednotebook import storage
from rednotebook.data import Day, Month


class TestCorruptedFileHandling:
    """Test handling of corrupted journal files."""

    def test_corrupted_file_with_null_characters(self):
        """Test that files with null characters are handled gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a normal journal file
            normal_file = os.path.join(tmpdir, "2024-10.txt")
            with open(normal_file, "w", encoding="utf-8") as f:
                f.write("1:\n  text: Normal entry\n")

            # Create a corrupted journal file with null characters
            corrupted_file = os.path.join(tmpdir, "2024-11.txt")
            with open(corrupted_file, "wb") as f:
                f.write(b"1:\n  text: Corrupted entry with \x00null character\n")

            # Load months - should not crash
            months, corrupted_files = storage.load_all_months_from_disk(tmpdir)

            # Normal file should be loaded
            assert "2024-10" in months
            assert len(months) == 1

            # Corrupted file should be detected and renamed
            assert len(corrupted_files) == 1
            original_path, corrupted_path = corrupted_files[0]

            assert original_path == corrupted_file
            assert corrupted_path.endswith("_corrupted.txt")
            assert os.path.exists(corrupted_path)
            assert not os.path.exists(corrupted_file)

    def test_multiple_corrupted_files_same_name(self):
        """Test handling multiple corrupted files with same base name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create first corrupted file
            corrupted_file1 = os.path.join(tmpdir, "2024-10.txt")
            with open(corrupted_file1, "wb") as f:
                f.write(b"corrupted content \x00")

            # Load once to create first _corrupted file
            storage.load_all_months_from_disk(tmpdir)

            # Create another corrupted file with same name
            corrupted_file2 = os.path.join(tmpdir, "2024-10.txt")
            with open(corrupted_file2, "wb") as f:
                f.write(b"different corrupted content \x00")

            # Load again - should create _corrupted_1 file
            months, corrupted_files = storage.load_all_months_from_disk(tmpdir)

            assert len(corrupted_files) == 1
            _, corrupted_path = corrupted_files[0]
            assert "_corrupted_1.txt" in corrupted_path

    def test_normal_yaml_errors_not_treated_as_corruption(self):
        """Test that normal YAML errors don't get treated as corruption."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file with invalid YAML syntax (but no null characters)
            invalid_file = os.path.join(tmpdir, "2024-10.txt")
            with open(invalid_file, "w", encoding="utf-8") as f:
                f.write("1:\n  text: Invalid YAML\n  missing_colon_here\n    - item\n")

            # Load months - should not rename the file
            months, corrupted_files = storage.load_all_months_from_disk(tmpdir)

            # No files should be detected as corrupted
            assert len(corrupted_files) == 0
            assert os.path.exists(invalid_file)  # Original file should still exist

    def test_save_load_compatibility(self):
        """Test that saving and loading still works with the new return format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a month with some data
            month = Month(2024, 12)
            day = Day(month, 25)
            day.text = "Christmas entry"
            month.days[25] = day
            month.edited = True

            # Save the month
            saved = storage._save_month_to_disk(month, tmpdir)
            assert saved

            # Load it back
            months, corrupted_files = storage.load_all_months_from_disk(tmpdir)

            # Verify the data is correct
            assert len(corrupted_files) == 0
            assert "2024-12" in months
            loaded_month = months["2024-12"]
            assert 25 in loaded_month.days
            assert loaded_month.days[25].text == "Christmas entry"
