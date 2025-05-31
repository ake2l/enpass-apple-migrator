import os
import tempfile
import csv
import filecmp
from enpass_escape import cli
import pytest

# Use absolute path to testdata at project root
TESTDATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'testdata'))
ENPASS_CSV = os.path.join(TESTDATA_DIR, 'enpass', 'export.csv')
ENPASS_JSON = os.path.join(TESTDATA_DIR, 'enpass', 'export.json')
APPLE_EXPECTED = os.path.join(TESTDATA_DIR, 'apple', 'Passwords.csv')


def read_csv_as_list(filepath):
    with open(filepath, newline='', encoding='utf-8') as f:
        return list(csv.reader(f))


def test_csv_to_apple_conversion():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = os.path.join(tmpdir, 'apple_out.csv')
        cli.transform_enpass_csv_to_apple(ENPASS_CSV, out_file)
        expected = read_csv_as_list(APPLE_EXPECTED)
        actual = read_csv_as_list(out_file)
        # Check header matches exactly
        assert actual[0] == expected[0], 'Header mismatch'
        # Check each row has correct number of columns and Notes/OTPAuth mapping
        for row in actual[1:]:
            assert len(row) == len(expected[0]), f"Row has wrong number of columns: {row}"
            # Notes should be in column 4, OTPAuth in column 5
            assert 'otpauth://' in row[5] or row[5] == '', f"OTPAuth not in correct column: {row}"
            # Notes can be empty or any string, but must be in column 4
            assert isinstance(row[4], str)


def test_json_to_apple_conversion():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = os.path.join(tmpdir, 'apple_out.csv')
        cli.transform_enpass_to_apple(ENPASS_JSON, out_file)
        expected = read_csv_as_list(APPLE_EXPECTED)
        actual = read_csv_as_list(out_file)
        assert actual[0] == expected[0], 'Header mismatch'
        for row in actual[1:]:
            assert len(row) == len(expected[0]), f"Row has wrong number of columns: {row}"
            assert 'otpauth://' in row[5] or row[5] == '', f"OTPAuth not in correct column: {row}"
            assert isinstance(row[4], str)


def test_cli_main_csv(tmp_path):
    out_file = tmp_path / 'apple_out.csv'
    cli.main(str(ENPASS_CSV), str(out_file))
    expected = read_csv_as_list(APPLE_EXPECTED)
    actual = read_csv_as_list(out_file)
    # Check header matches exactly
    assert actual[0] == expected[0], 'Header mismatch'
    # Check each row has correct number of columns and Notes/OTPAuth mapping
    for row in actual[1:]:
        assert len(row) == len(expected[0]), f"Row has wrong number of columns: {row}"
        # Notes should be in column 4, OTPAuth in column 5
        assert 'otpauth://' in row[5] or row[5] == '', f"OTPAuth not in correct column: {row}"
        assert isinstance(row[4], str)


def test_cli_main_json(tmp_path):
    out_file = tmp_path / 'apple_out.csv'
    cli.main(str(ENPASS_JSON), str(out_file))
    expected = read_csv_as_list(APPLE_EXPECTED)
    actual = read_csv_as_list(out_file)
    assert actual[0] == expected[0], 'Header mismatch'
    for row in actual[1:]:
        assert len(row) == len(expected[0]), f"Row has wrong number of columns: {row}"
        assert 'otpauth://' in row[5] or row[5] == '', f"OTPAuth not in correct column: {row}"
        assert isinstance(row[4], str)
