import argparse
import calendar
from datetime import date, timedelta
from typing import Callable, Tuple

from idid import cli
import pytest


def get_dates(text: str) -> Tuple[Tuple[cli.DateRange], Tuple[Callable[[str], bool]]]:
    parser = argparse.ArgumentParser()
    for k, v in cli.parser_options(["-d", "-r", "-x", "-f", "-v"]):
        parser.add_argument(k, **v)
    args = parser.parse_args(text.split())
    return cli.parse_entry_args(args)


def days_ago(days_ago: int) -> date:
    return date.today() - timedelta(days=days_ago)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("-d 0", days_ago(0)),
        ("-d 1", days_ago(1)),
        ("-d today", days_ago(0)),
        ("-d yesterday", days_ago(1)),
        ("-d 2020-08-01", date(2020, 8, 1)),
        ("-d 20200801", date(2020, 8, 1)),
        ("-d 01-01", date(date.today().year, 1, 1)),
        ("-d 0101", date(date.today().year, 1, 1)),
        ("-d 12-31", date(date.today().year - 1, 12, 31)),
        ("-d 1231", date(date.today().year - 1, 12, 31)),
    ],
)
def test_cli_parse_date(text: str, expected: date):
    """Date by interger 'days ago'."""
    dates, preds = get_dates(text)
    assert len(dates) == 1
    assert len(preds) == 1  # The default predicate
    assert dates[0].begin == expected
    assert dates[0].close == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("-d 0,today", days_ago(0)),
        ("-d 1,yesterday", days_ago(1)),
    ],
)
def test_cli_get_days_ago_multiple(text: str, expected: date):
    dates = get_dates(text)[0]  # I only care about the dates
    assert len(dates) == 2
    assert dates[0] == dates[1]
    assert dates[0].begin == expected
    assert dates[0].close == expected


@pytest.mark.parametrize(
    "text,dow,multiplier",
    [
        ("-d sun", 6, 1),
        ("-d sun0", 6, 1),
        ("-d sun1", 6, 1),
        ("-d sun4", 6, 4),
        ("-d wed", 2, 1),
    ],
)
def test_cli_dow(text: str, dow: int, multiplier: int):
    dates = get_dates(text)[0]
    assert len(dates) == 1
    assert dates[0].days == 1
    assert dates[0].begin.weekday() == dow
    assert (date.today() - dates[0].begin).days <= (7 * multiplier)
    assert (date.today() - dates[0].begin).days > (7 * (multiplier - 1))


def test_cli_last_week_starting_today():
    dow = date.today().weekday()
    dates = get_dates(f"-d {calendar.day_abbr[dow]} -vv")[0]
    assert len(dates) == 1
    assert dates[0].days == 1
    assert dates[0].begin.weekday() == dow
    assert (date.today() - dates[0].begin).days == 7


@pytest.mark.parametrize(
    "text,begin,close",
    [
        ("-r 2020-01-01 7", date(2020, 1, 1), date(2020, 1, 7)),
        ("-r 6 today", days_ago(6), days_ago(0)),
    ],
)
def test_cli_range(text: str, begin: date, close: date):
    dates, preds = get_dates(text)
    assert len(dates) == 1
    assert len(preds) == 1
    assert dates[0].begin == begin
    assert dates[0].close == close
    assert dates[0].days == 7


@pytest.mark.parametrize(
    "text,error_says",
    [
        ("-r day 1", "is invalid"),
        ("-r 6 day", "is invalid"),
        ("-r 20200101 1010", "must be less than 1000"),
    ],
)
def test_cli_range_exceptions(text: str, error_says: str):
    with pytest.raises(Exception) as err:
        get_dates(text)
    assert error_says in str(err.value)


def test_cli_range_0_days_is_invalid():
    with pytest.raises(Exception):
        get_dates("-r 6 0")


def test_cli_range_day_length():
    dates = get_dates("-r 6 3")[0]
    assert dates[0].days == 3


def test_cli_range_in_chronological_order():
    get_dates("-r sun2 sun")[0]
    with pytest.raises(Exception) as err:
        get_dates("-r sun sun2")
    assert "Did you mean '-r " in str(err.value)


@pytest.mark.parametrize(
    "cmd,text,expect",
    [
        ("-f find", "find this", True),
        ("-f find", "unfound", False),
    ],
)
def test_cli_find(cmd, text, expect):
    preds = get_dates(cmd)[1]
    assert expect == all(_(text) for _ in preds)


@pytest.mark.parametrize(
    "cmd,text,expect",
    [
        ("-x @is", "This @is personal", False),
        ("-x @is", "This is personal", True),
        ("-x bad", "This is bad", False),
    ],
)
def test_cli_exclude(cmd: str, text: str, expect: bool):
    preds = get_dates(cmd)[1]
    assert expect == all(_(text) for _ in preds)


def test_parse_dow_wo_match():
    d = cli.parse_dow("junk")
    assert d is None


def test_parse_yyyy_mm_dd_wo_relative():
    d = cli.parse_yyyy_mm_dd("0101")
    today = date.today()
    assert d is not None
    assert d.year == today.year
