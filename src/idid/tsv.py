"""Get IDid entries from one or more DateRanges."""
import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Callable, Generator, List, Sequence
from idid.entry import Entry


__all__ = ["DateRange", "Entries", "get_entries", "get_entries_from", "get_default_TSV"]

Entries = Sequence[Entry]


def get_default_TSV() -> Path:
    """Get a path to a TSV either from environment or .local/share."""
    return Path(os.getenv("ididTSV", "~/.local/share/idid/idid.tsv")).expanduser()


def get_default_start_text() -> str:
    """Get the text indicating the start of the day."""
    return os.getenv("ididSTART", "*~*~*--------------------")


@dataclass
class DateRange:
    """DateRange starting from `begin` through and including `close`."""

    begin: date
    close: date

    @property
    def days(self) -> int:
        """Number of days included in this range.

        Examples:
          >>> DateRange(date(2020,1,1), date(2020,1,1)).days
          1
          >>> DateRange(date(2020,1,1), date(2020,1,7)).days
          7
        """
        return (self.close - self.begin).days + 1

    def __contains__(self, timestamp: datetime) -> bool:
        """Is the timestamp in the range of dates.

        Args:
            timestamp: the datetime in question.
        """
        return self.begin <= timestamp.date() <= self.close

    def __repr__(self):
        """Show date or range.

        Examples:
          >>> DateRange(date(2020,1,2), date(2020,1,2))
          20Jan02Thu
          >>> DateRange(date(2020,1,1), date(2020,1,7))
          20Jan01Wed-20Jan07Tue
        """
        b = self.begin.strftime("%y%b%d%a")
        if self.begin == self.close:
            return b
        return f"{b}-{self.close.strftime('%y%b%d%a')}"

    def __len__(self):
        """The number of days in this DateRange."""
        return self.days

    def __lt__(self, other):
        """Does this DateRange begin another.

        Args:
            other: comparison DateRange
        """
        return self.begin < other.begin


def reverse_readline(path: Path, buf_size: int = 8192):
    """A generator returning the lines of a file in reverse order.

    Args:
        path : A TSV file.
        buf_size: working buffer of 8192 by default.

    Returns:
        A single line from a TSV file.

    Example:
        last = reverse_readline("~/.local/share/idid-cli/idid.tsv")
    """
    with open(path) as fh:  # no cov
        segment = None
        offset = 0
        fh.seek(0, os.SEEK_END)
        file_size = remaining_size = fh.tell()
        while remaining_size > 0:
            offset = min(file_size, offset + buf_size)
            fh.seek(file_size - offset)
            buffer = fh.read(min(remaining_size, buf_size))
            remaining_size -= buf_size
            lines = buffer.split("\n")
            # The first line of the buffer is probably not a complete line so
            # we'll save it and append it to the last line of the next buffer
            # we read
            if segment is not None:
                # If the previous chunk starts right from the beginning of line
                # do not concat the segment to the last line of new chunk.
                # Instead, yield the segment first
                if buffer[-1] != "\n":
                    lines[-1] += segment
                else:
                    yield segment
            segment = lines[0]
            for index in range(len(lines) - 1, 0, -1):
                if lines[index]:
                    yield lines[index]
        # Don't yield None if the file was empty
        if segment is not None:
            yield segment


def get_entries(
    date_ranges: Sequence[DateRange],
    filters: Sequence[Callable[[str], bool]] = (lambda _: True,),
    source: Generator[str, None, None] = reverse_readline(get_default_TSV()),
) -> List[Entry]:
    """Entries from source on `date_ranges` and `filters`.

    Args:
      date_ranges: a sequence of `DateRange`
      filters: Callable against Entry.text; default all
      source: tsv lines is descending cronological order
    """
    matching: List[Entry] = []
    ranges = list(date_ranges)
    if len(ranges) == 0:
        return matching

    ranges.sort()
    last_entry = None

    default_start_text = get_default_start_text()

    def is_start(e: Entry) -> bool:
        """This entry is the beginning of tracking and not a continuation."""
        return e.text.startswith(default_start_text)

    ## Go line by line in reverse order
    for line in source:
        entry = Entry.from_tsv(line)

        # The last entry began when this one ceased
        if last_entry is not None:
            last_entry.begin = entry.cease

        if (
            last_entry is not None
            and not is_start(last_entry)
            and any(last_entry.begin in r for r in ranges)
            and all(_(last_entry.text) for _ in filters)
        ):
            matching.append(last_entry)

        # Stop when dates are before any date of interest
        if entry.cease.date() < ranges[0].begin:
            break

        # A start entry can not be used in the last entry
        last_entry = None if is_start(entry) else entry

    # Matched in reverse order, return in chronological order
    matching.sort()
    return matching


def get_entries_from(
    path: Path,
    date_ranges: Sequence[DateRange],
    filters: Sequence[Callable[[str], bool]] = (lambda _: True,),
) -> List[Entry]:
    """Get Entries matching both `date_ranges` and `filters`.

    Args:
        path: the TSV file path
        date_ranges: all date ranges of interest
        filters: filters on Entry.text
    """
    return get_entries(date_ranges, filters, reverse_readline(path))


#######################
## Move to tt-reports

# def primary_grouping(entries: Iterable[Entry]) -> Dict[str, List[Entry]]:
#    """Group projects by the first @project in text."""
#    projects = defaultdict(list)
#    for entry in entries:
#        projects[entry.primary()].append(entry)
#    return projects
#
#
# def sum_duration(entries: Iterable[Entry]) -> timedelta:
#    """Total time of given all Entry.
#
#    Args:
#      entries : iterable of valid Entry
#
#    Returns:
#      timedelta
#    """
#    return sum((x.duration() for x in entries), timedelta(0))
#
#
# def primary_totals(groupings: Dict[str, List[Entry]]):  # -> Dict[str, timedelta]:
#    """Get the primary totals for each grouping."""
#    return {
#        k: sum((x.duration() for x in v), timedelta()) for (k, v) in groupings.items()
#    }
#
