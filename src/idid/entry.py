"""An IDid entry and helpers."""
from dataclasses import dataclass
from datetime import datetime, timedelta

__all__ = ["Entry", "h_mm", "round_timedelta"]


@dataclass(order=True)
class Entry:
    """A recorded accomplishment entry."""

    begin: datetime
    cease: datetime
    text: str

    @property
    def duration(self) -> timedelta:
        """Duration from begin to cease."""
        return self.cease - self.begin

    def __repr__(self) -> str:
        """Show the date, cease, duration, and text.

        >>> repr(Entry(datetime(2020,1,1,1,2), datetime(2020,1,1,2,3), "Test"))
        'Jan01Wed 02:03(1:01)Test'
        """
        return "{} {}({}){}".format(
            self.cease.strftime("%b%d%a"),
            self.cease.time().isoformat("minutes"),
            h_mm(self.duration),
            self.text,
        )

    @classmethod
    def from_tsv(cls, tsv_line: str):
        """Create an Entry from a tsv line."""
        cease_text, text = tsv_line.split("\t")
        cease_timestamp = datetime.fromisoformat(cease_text)
        return Entry(cease_timestamp, cease_timestamp, text)


def round_timedelta(d: timedelta, nearest=60) -> timedelta:
    """Round timedelta to the nearest `seconds`.

    With nearest of 60 seconds, round to nearest minute.

    Examples:
        >>> round_timedelta(timedelta(seconds=89))
        datetime.timedelta(seconds=60)
        >>> round_timedelta(timedelta(seconds=90))
        datetime.timedelta(seconds=120)
        >>> round_timedelta(timedelta(seconds=91))
        datetime.timedelta(seconds=120)
        >>> round_timedelta(timedelta(seconds=29), 30)
        datetime.timedelta(seconds=30)
        >>> round_timedelta(timedelta(seconds=31), 30)
        datetime.timedelta(seconds=30)

    Args:
      d : A datetime.timedelta
      nearest : Number of seconds; default of 60 rounds to nearest minute.

    """
    seconds = d.seconds
    rounding = (seconds + nearest / 2) // nearest * nearest
    return d + timedelta(0, rounding - seconds, 0)


def h_mm(d: timedelta) -> str:
    """Stringify a timedelta rounded to the nearest minute.

    Examples:
        >>> h_mm(timedelta(seconds=45))
        '0:01'
        >>> h_mm(timedelta(seconds=5000))
        '1:23'
        >>> h_mm(timedelta(hours=30.75))
        '30:45'
    """
    t = round_timedelta(d)
    h = int(t.total_seconds() / 3600)
    m = int((t.total_seconds() % 3600) / 60)
    return f"{h}:{m:02}"
