"""Select either individual dates or a range of dates.

A date is one of the following:

1. Number of days in the past; zero is today and one is yesterday.
2. Literal text of 'today' or 'yesterday'.
3. ISO 8601 date format 'YYYY-MM-DD' or 'MM-DD' within the last year.
   Dashes are optional.
4. The locale abbreviated, last day-of-the-week. A suffix adds weeks.
   'mon' and 'mon1' mean the same and 'mon2' is two Mondays ago.

A range is either a start date and end date, or a start date and number of
days to include. The end date can not be the number of days before today.

args = idid.cli.get_parser().parse_args()
"""
import argparse
import locale
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Callable, List, Optional, Tuple
from idid.tsv import DateRange, Entries, get_default_TSV, get_entries_from

# from typing import Callable, Iterable, Dict, List, Tuple, Generator, Sequence

__all__ = [
    "DateRange",
    "parser_options",
    "parse_entry_args",
    "parse_filters",
    "text_to_date",
]

"""
Module that contains the command line app.

Why does this file exist, and why not put this in __main__?

  You might be tempted to import things from __main__ later, but that will cause
  problems: the code will get executed twice:

  - When you run `python -midid` python will execute
    ``__main__.py`` as a script. That means there won't be any
    ``idid.__main__`` in ``sys.modules``.
  - When you import __main__ it will get executed again (as a module) because
    there's no ``idid.__main__`` in ``sys.modules``.

  Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""

# Matches one of: YYYY-MM-DD, YYYYMMDD, MM-DD, MMDD
# match groups 1=YYYY, 3=MM, 4=DD, or 5=MM, 7=DD
_regex_yyyy_mm_dd = re.compile(
    r"^(\d{4})(-?)(0[1-9]|1[0-2])\2([12]\d|0[1-9]|3[01])|(0[1-9]|1[0-2])(-?)([12]\d|0[1-9]|3[01])$"
)

# List of abbreviated, locale days-of-the-week starting with Monday
_dow_locale = [
    locale.nl_langinfo(getattr(locale, f"ABDAY_{x}")).lower()
    # ISO order with Monday first
    for x in (2, 3, 4, 5, 6, 7, 1)
]

# Matches abbreviated day-of-the-week with optional number suffix
_regex_dow = re.compile(f"({'|'.join(_dow_locale)})([0-9]*)", re.ASCII)


def parse_yyyy_mm_dd(text: str, relative: Optional[date] = None) -> Optional[date]:
    """Parse the ISO 8601 text to a date.

    Args:
      text: one of: YYYY-MM-DD, YYYYMMDD, MM-DD, or MMDD
      relative: find MM-DD relative to date, default is today

    Examples:
      >>> parse_yyyy_mm_dd('0401',date(2020,6,1))
      datetime.date(2020, 4, 1)
      >>> parse_yyyy_mm_dd('0801',date(2020,6,1))
      datetime.date(2019, 8, 1)
      >>> parse_yyyy_mm_dd('08-01',date(2020,6,1))
      datetime.date(2019, 8, 1)
      >>> parse_yyyy_mm_dd('06-01',date(2020,6,1))
      datetime.date(2019, 6, 1)
      >>> parse_yyyy_mm_dd('2019-08-01',date(2020,6,1))
      datetime.date(2019, 8, 1)
      >>> parse_yyyy_mm_dd('20190801',date(2021,6,1))
      datetime.date(2019, 8, 1)
      >>> parse_yyyy_mm_dd('2019-0801',date(2020,6,1)) is None
      True
    """
    match = re.fullmatch(_regex_yyyy_mm_dd, text)

    if not match:
        return None

    if match.group(1):  # Year is given
        return date(
            int(match.group(1)),
            int(match.group(3)),
            int(match.group(4)),
        )  # day

    if relative is None:
        relative = date.today()

    day = date(relative.year, int(match.group(5)), int(match.group(7)))
    if day >= relative:
        day = date(relative.year - 1, day.month, day.day)
    return day


def parse_dow(text: str, relative: Optional[date] = None) -> Optional[date]:
    """Parse abbreviated, locale day-of-the-week.

    Args:
      text: abbreviated, locale day-of-the-week, ie 'mon', 'tue', ...
        A suffix goes back a number of weeks. Both "mon" and "mon1"
        mean last Monday, while "mon4" is four Mondays ago
      relative: the relative date used, usually today

    Examples:
      >>> parse_dow("mon", date(2020, 4, 1))
      datetime.date(2020, 3, 30)
      >>> parse_dow("fri", date(2020, 4, 2))
      datetime.date(2020, 3, 27)
      >>> parse_dow("mon2", date(2020, 4, 2))
      datetime.date(2020, 3, 23)
      >>> parse_dow("fri2", date(2020, 4, 1))
      datetime.date(2020, 3, 20)
      >>> parse_dow("mon4", date(2020, 3, 31))
      datetime.date(2020, 3, 9)
      >>> parse_dow("fri4", date(2020, 3, 31))
      datetime.date(2020, 3, 6)
    """
    match = _regex_dow.fullmatch(text.lower())

    if not match:
        return None

    if relative is None:
        relative = date.today()

    days = get_last_dow(_dow_locale.index(match.group(1)), relative.weekday())
    if match.group(2):
        days += 7 * max(0, int(match.group(2)) - 1)

    return relative - timedelta(days=days)


def text_to_date(text: str, relative: Optional[date] = None) -> Optional[date]:
    """Parse the give date string.

    Args:
      text: the text to parse and is one of
        Number of days before today; zero is today and one is yesterday.
        Literal text of 'today' or 'yesterday'.
        ISO 8601 date format 'YYYY-MM-DD' or 'MM-DD' within the last 364 days.
            Dashes are optional.
        The locale abbreviated, last day-of-the-week. A suffix adds weeks.
            'mon' and 'mon1' is last Monday and 'mon2' is two Mondays ago.
      relative: the relative date used, usually today
    """
    today = relative if relative is not None else date.today()
    # Make sure it doesn't look like MMDD
    if text.isdigit() and len(text) < 4:
        return today - timedelta(days=int(text))

    # All text comparison will be lower case
    text = text.lower()

    # Named days "today" and "yesterday"
    if text == "today":
        return today

    elif text.startswith("yester"):
        return today - timedelta(days=1)

    # Looks like a specific date
    elif text[0:2].isdigit():
        given_date = parse_yyyy_mm_dd(text, today)
        if given_date is not None:
            return given_date

    else:
        return parse_dow(text)


def make_date_range(begin: str, through: str) -> DateRange:
    """Create a date range using CLI strings."""
    starting = text_to_date(begin)
    end_on = text_to_date(through)
    assert starting is not None
    assert end_on is not None
    return DateRange(text_to_date(begin), text_to_date(through))


def get_last_dow(look_for: int, relative: int) -> int:
    """Get the number of days before relative DOW

    Args:
      look_for: DOW, 0=Monday, 6=Sunday; datetime.date.weekday()
      relative: DOW, 0=Monday, 6=Sunday; datetime.date.weekday()

    Returns:
      The number of days before relative to reach look_for.

    Examples:
      >>> get_last_dow(2, 2)  # Wednesday relative to Wednesday
      7
      >>> get_last_dow(0, 2)  # Monday relative to Wednesday
      2
      >>> get_last_dow(4, 2)  # Friday relative to Wednesday
      5
    """

    days = relative - look_for
    if days <= 0:
        days = 7 - look_for + relative
    return days


TSV_EXTRACT = ["-d", "-r", "-f", "-x", "--tsv"]


def parser_options(
    options: Optional[List[str]] = None, tsv=None
) -> List[Tuple[str, dict]]:
    """Get standard command-line options.
        -d  number of DAYS earlier, DOW[n], or [YYYY]MM-DD"
        -r  from DATE through DAYS or DATE
        -f  find entries matching REGEX
        -x  exclude entries matching REGEX
        -v  verbose, multiple entries is more verbose
        --tsv  IDid tab separated time file

    Args:
        options: One or more of: -d, -r, -f, -x, -v, --tsv

    Example:
        for name, attrib in parser_options():
            parser.add_argument(name, **attrib)

    >>> [name for name, options in parser_options()]
    ['-d', '-r', '-f', '-x', '--tsv']
    >>> [name for name, options in parser_options(['-d','-r','--tsv'])]
    ['-d', '-r', '--tsv']
    """
    if tsv is None:
        tsv = get_default_TSV()
    known = {
        "--tsv": {
            "type": Path,
            "default": tsv,
            "help": f"default {tsv}",
        },
        "-d": {
            "action": "append",
            "dest": "date",
            "metavar": "DATE[,DATE]",
            "help": "number of DAYS earlier, DOW[n], [YYYY]MMDD",
        },
        "-r": {
            "action": "append",
            "dest": "range",
            "nargs": 2,
            "metavar": "DATE",
            "help": "from DATE through DATE/DAYS",
        },
        "-f": {
            "dest": "find",
            "metavar": "REGEX",
            "help": "find entries matching REGEX",
        },
        "-x": {
            "dest": "exclude",
            "metavar": "REGEX",
            "help": "exclude entries matching REGEX",
        },
        "-v": {
            "action": "count",
            "dest": "verbose",
            "default": 0,
            "help": "Verbose, multiple for more verbose",
        },
    }

    # Assume TSV processing
    if options is None:
        options = TSV_EXTRACT

    # Use List instead or OrderedDict
    return [(k, known[k]) for k in options if k in known]


def parse_date_ranges(args: argparse.Namespace) -> Tuple[DateRange]:
    date_ranges = []
    if hasattr(args, "date") and args.date:
        for arg_item in args.date:
            for item in arg_item.split(","):
                d = text_to_date(item)
                if d is not None:
                    date_ranges.append(DateRange(d, d))

    if hasattr(args, "range") and args.range:
        for text, days in args.range:
            start = text_to_date(text)
            if start is None:
                raise Exception(f"'{text}' is invalid")

            if not days.isdigit():
                end = text_to_date(days)
                if end is None:
                    raise Exception(f"'{days} is invalid")
            else:
                days = int(days)
                if days <= 0:
                    raise Exception(f"'{days}' must be positive number")
                elif days > 999:  # Anything larger looks like MMDD
                    raise Exception(f"'{days}' must be less than 1000")
                else:
                    end = start + timedelta(days=days - 1)
            if start > end:
                raise Exception(f"Did you mean '-r {end} {start}' dates reversed?")

            date_ranges.append(DateRange(start, end))
    date_ranges.sort()
    return tuple(date_ranges)


def parse_filters(exclude: str, include: str) -> Tuple[Callable[[str], bool]]:
    """Created callables testing if text should be selected.

    Include or exclude based on regex pattern search. However, if the
    first character is '+' or '*', treat it as a literal.
    With empty excludes and includes, accept everything.

    Args:
      excludes: regex
      includes: regex

    Examples:
      >>> all(_('+proj bad commit') for _ in parse_filters(None,None))
      True
      >>> [_('+proj bad commit') for _ in parse_filters('bad',None)]
      [False]
      >>> [_('+proj bad commit') for _ in parse_filters('bogus', '+proj')]
      [True, True]
      >>> [_('+proj bad commit') for _ in parse_filters('+proj', 'jidn')]
      [False, False]
    """

    checks = []

    # Return `found` when `pattern` is found
    def on_search(pattern: str, found: bool):
        """Return value if `pattern` is found."""
        # Now todo.txt users have it easier
        escape = ("+", "*")
        if pattern[0] in escape:
            pattern = "\\" + pattern

        regex_pattern = re.compile(pattern)
        if found:
            return lambda _: regex_pattern.search(_) is not None
        return lambda _: regex_pattern.search(_) is None

    # Pattern is not allowed
    if exclude is not None:
        checks.append(on_search(exclude, False))

    # Pattern is required
    if include is not None:
        checks.append(on_search(include, True))

    # No patterns, accept everything
    if len(checks) == 0:
        checks.append(lambda _: True)
    return tuple(checks)


def parse_entry_args(
    args: argparse.Namespace,
) -> Tuple[Tuple[DateRange], Tuple[Callable[[str], bool]]]:
    """Get date ranges and selection filters, if any.

    Args:
        args: ArgumentParser.parse_args() Namespace or None

    See:
        parse_date_ranges()
        parse_filters()

    Example:
        date_ranges, filters = parse_entry_args(parse.parse_args())
    """

    date_ranges = parse_date_ranges(args)
    if hasattr(args, "verbose") and args.verbose > 1:
        print(f"For date ranges: {', '.join(str(_) for _ in date_ranges)}")

    filters = parse_filters(args.exclude, args.find)
    return date_ranges, filters


def get_entries_from_args(args: argparse.Namespace) -> Entries:
    """Get entries from argparse.Namespace.

    Args
        args: ArgumentParser.parse_args() Namespace or None
    """

    return get_entries_from(args.tsv, *parse_entry_args(args))
