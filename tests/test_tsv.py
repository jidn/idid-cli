import argparse
from typing import Callable, Tuple
from datetime import date, datetime, timedelta
from pathlib import Path
from idid import cli, tsv


def test_daterange_repr():
    today = date.today()
    today_dr = tsv.DateRange(today, today)
    today_repr = repr(today_dr)
    assert "-" not in today_repr
    assert today.day == int(today_repr[5:7])

    yesterday = today - timedelta(days=1)
    dr = repr(tsv.DateRange(yesterday, today)).split("-")
    assert dr[0] != dr[1]


def test_daterange_lt():
    today = date.today()
    today_dr = tsv.DateRange(today, today)

    yesterday = today - timedelta(days=1)
    yesterday_dr = tsv.DateRange(yesterday, today)

    assert yesterday_dr < today_dr


def test_daterange_len():
    today = date.today()
    assert 1 == len(tsv.DateRange(today, today))
    assert 2 == len(tsv.DateRange(today - timedelta(days=1), today))


def test_default_start_text():
    assert tsv.get_default_start_text().startswith("*~*~*")


def data_idid_tsv_path() -> Path:
    """Get the TSV path used in testing."""
    return Path(__file__).parent / "data" / "idid.tsv"


def from_cmd(
    command_line: str,
) -> Tuple[Tuple[tsv.DateRange], Tuple[Callable[[str], bool]]]:
    parser = argparse.ArgumentParser()
    for k, v in cli.parser_options():
        parser.add_argument(k, **v)

    args = parser.parse_args(command_line.split())
    return cli.parse_entry_args(args)


def test_get_day_all():
    tsv_path = data_idid_tsv_path()
    days, filters = from_cmd("-d 2021-10-22")
    entries = tsv.get_entries(days, filters, tsv.reverse_readline(tsv_path, 64))

    assert 1 == len(filters)
    assert 7 == len(entries)
    assert datetime(2021, 10, 22, 7, 58, 55) == entries[0].begin.replace(tzinfo=None)


def test_get_day_exclude():
    tsv_path = data_idid_tsv_path()
    days, filters = from_cmd("-d 20211022 -x lunch")
    entries = tsv.get_entries_from(tsv_path, days, filters)

    assert 1 == len(filters)
    assert 6 == len(entries)


def test_get_no_entries():
    tsv_path = data_idid_tsv_path()
    entries = tsv.get_entries([], [], tsv.reverse_readline(tsv_path, 128))

    assert [] == entries
