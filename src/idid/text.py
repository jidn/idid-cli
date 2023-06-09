"""Create simple test reports.

Use ReportDetail() to see each entries text description.
Use ReportSummary() to group each day and show the total for the day.
"""

from datetime import datetime, timedelta  # datetime.datetime used in doctest
from collections import defaultdict
import textwrap
from typing import List, Sequence, Tuple
from idid.entry import Entry, h_mm


def BeganEndedDuration(
    entries: Sequence[Entry],
    width: int = 80,
    separators=("  ", "  "),
    titles=("Began", "Ended", "Hours"),
) -> Tuple[List[str], int]:
    """Print sequence of entries.

    Args:
        entries: entries to use
        width: of the report output in characters
        separators: tuple(str between fields, str before text)
        titles: field headers

    Example:
        Began  Ended  Hours  [Mon, Jan 1]
        -----  -----  -----
        08:01  10:11   2:10  Fixed #101038
        10:11  11:57   1:46  Fixed #101039

    """
    output = []
    widths = [len(_) for _ in titles]
    title = separators[0].join(titles)
    # Title of first entry.begin day
    title += separators[1] + f"[{entries[0].begin:%a, %b %d}]"
    output.append(title)
    # Title under dashes
    output.append(separators[0].join("-" * _ for _ in widths))

    # Space taken for up to the end of the hours
    fields_width = sum(widths) + (2 * len(separators[0]))
    widths.append(width - (fields_width + len(separators[1])))
    output.extend(_BeganEndedDurationFormat(entries, tuple(widths), separators))
    return output, fields_width


def _BeganEndedDurationFormat(
    entries: Sequence[Entry], width: Sequence[int], separators: Sequence[str]
) -> List[str]:
    """Print a sequence of entries: begin, cease, duration, text.

    Args:
      entries: list of entries to report
      width: width of report
      separators: tuple(str between fields, str before text)

    >>> e = Entry(datetime(2020,1,2,8,1), datetime(2020,1,2,10,11), "Fixed #101038")
    >>> _BeganEndedDurationFormat([e], (5,5,5,59), ('  ','  '))
    ['08:01  10:11   2:10  Fixed #101038']
    """
    output = []
    fields_width = sum(width[:-1]) + (len(separators[0] * (len(width) - 2)))
    text_width = width[-1]
    for e in entries:
        txt = textwrap.wrap(e.text, text_width)
        fields = separators[0].join(
            (f"{e.begin:%H:%M}", f"{e.cease:%H:%M}", f"{h_mm(e.duration)}")
        )
        output.append(separators[1].join((fields, txt[0])))
        for t in txt[1:]:
            output.append(f"{'':{fields_width}s}{separators[1]}{t}")
    return output


def ReportDetail(
    entries: Sequence[Entry], width: int = 80, separators=("  ", "  ")
) -> List[str]:
    """Daily report.

    Args:
        entries: list of entries to report
        width: width of report
        separators: tuple(str between fields, str before text)

    Example:
        Began  Ended  Hours  [Mon, Jan 1]
        -----  -----  -----
        08:01  10:11   2:10  Fixed #101038
        10:11  11:57   1:46  Fixed #101039
        ============   3:46

    """
    if len(entries) == 0:
        return []

    entries = sorted(entries)
    output, fields_width = BeganEndedDuration(entries, width, separators)
    total = sum((x.duration for x in entries), timedelta())
    output.append(f"{'='*(fields_width-7)} {h_mm(total):>6}")
    return output


def ReportDaySummary(entries: Sequence[Entry]) -> List[str]:
    """Daily summary.

    Args:
        entries: list of entries to report

    Example:
        Wed, Jan 01    8:15
        Thu, Jan 02   10:05
        Fri, Jan 03    7:47
        ============  26:07
    """
    dailies = defaultdict(list)
    for e in entries:
        dailies[e.begin.date()].append(e)
    output = []
    totals = []
    for day in sorted(dailies.keys()):
        total = sum((x.duration for x in dailies[day]), timedelta())
        output.append(f"{day:%a, %b %d}  {h_mm(total):>6}")
        totals.append(total)
    grand_total = sum((x.duration for x in entries), timedelta())
    output.append(f"============{h_mm(grand_total):>7}")
    return output
