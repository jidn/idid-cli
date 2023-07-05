"""Process command line entry arguments."""
import argparse
import datetime
import re
from pathlib import Path
from stat import S_IRWXU
from sys import exit
from typing import List, Optional

from idid import cli, tsv, text
from idid.entry import Entry, h_mm


def parse_time(text: str, relative: Optional[datetime.datetime]) -> datetime.datetime:
    """Parse test to a datetime.timedelta.

    [minutes] in the past
    [HH:MM] with optional "am" or "pm"

    Args:
        text: either [minutes] or [HH:MM]am|pm
        relative: to what datetime should the text be parsed; default is now

    >>> parse_time('',datetime.datetime(2023,1,1,12,0,0))
    datetime.datetime(2023, 1, 1, 12, 0)
    >>> parse_time('90',datetime.datetime(2023,1,1,12,0,0))
    datetime.datetime(2023, 1, 1, 10, 30)
    >>> parse_time('9:30',datetime.datetime(2023,1,1,12,0,0))
    datetime.datetime(2023, 1, 1, 9, 30)
    >>> parse_time('09:30pm',datetime.datetime(2023,1,1,12,0,0))
    datetime.datetime(2023, 1, 1, 21, 30)
    >>> parse_time('21:30',datetime.datetime(2023,1,1,12,0,0))
    datetime.datetime(2023, 1, 1, 21, 30)
    """
    if relative is None:
        relative = datetime.datetime.now().astimezone()  # python 3.6
    if not text:
        return relative
    elif text.isnumeric():
        return relative - datetime.timedelta(minutes=int(text))

    regex = re.compile(r"(0?\d|1\d|2[0-3]):([0-5]\d)(am|pm)?", re.ASCII)
    match = regex.fullmatch(text)
    if not match:
        print(f"Unable to parse '{text}' as -t WHEN parameter.")
        exit(1)

    hour = int(match.group(1))
    minutes = int(match.group(2))
    if hour < 12 and match.group(3) is not None and match.group(3)[0] == "p":
        hour += 12
    return relative.replace(hour=hour, minute=minutes)


def add_to_tsv(text: List[str], path: Path, at_time: datetime.datetime) -> None:
    """Add entry to TSV."""
    attempts = 0
    iso_format = at_time.isoformat(" ", "seconds")
    line = " ".join(text)

    def write_accomplishment():
        with open(path, "ta") as tsv:
            tsv.write(f"{iso_format}\t{line}\n")

    while True:
        try:
            return write_accomplishment()
        except FileNotFoundError as ex:
            attempts += 1
            if attempts > 2:
                raise ex
            print(f"creating {path}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch(S_IRWXU, exist_ok=True)


def edit_tsv(path: Path) -> bool:
    """Open path with EDITOR.

    Args:
        path: TSV file
    """
    import os

    editor = os.getenv("EDITOR")
    if not editor:
        return False
    else:
        import subprocess

        # Assume vim deritive, go to end of file.
        subprocess.run([editor, str(path), "+$"])
        return True


def create_parser() -> argparse.ArgumentParser:
    """Create CLI parser to start, create, or select entries."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "text",
        **{
            "metavar": "TEXT",
            "nargs": "*",
            "help": "Record accomplishment",
        },
    )
    parser.add_argument(
        "-s", **{"dest": "start", "action": "store_true", "help": "Start your day."}
    )
    parser.add_argument(
        "-t", **{"dest": "when", "help": "Record either WHEN minutes ago or HH:MM."}
    )
    for k, v in cli.parser_options(["-d", "-r", "-x", "-f", "-v", "--tsv"]):
        parser.add_argument(k, **v)

    parser.add_argument(
        "-e",
        **{
            "dest": "edit",
            "action": "store_true",
            "help": "Edit the TSV file using EDITOR",
        },
    )
    return parser


def show_entries(args):
    """Show either a day's detail or days summary."""
    from os import linesep

    try:
        date_ranges, filters = cli.parse_entry_args(args)
    except argparse.ArgumentError as err:
        print(err)
        exit(1)

    entries = tsv.get_entries_from(args.tsv, date_ranges, filters)
    if len(entries) > 0:
        if len(date_ranges) == 1 and date_ranges[0].days == 1:
            print(*text.ReportDetail(entries), sep=linesep)
        else:
            print(*text.ReportDaySummary(entries), sep=linesep)


def main():
    """Handle CLI argument processing."""
    parser = create_parser()

    args = parser.parse_args()
    if args.verbose > 1:
        print(args)

    if args.edit:
        edit_tsv(args.tsv)
    elif args.start:
        at_time = parse_time(args.when, None)
        add_to_tsv([tsv.get_default_start_text()], args.tsv, at_time)
        if args.verbose > 0:
            print(f"Thank you. Started at {at_time:%H:%M}.")
    elif args.text:
        at_time = parse_time(args.when, None)
        add_to_tsv(args.text, args.tsv, at_time)
        if args.verbose > 0:
            print(at_time.isoformat(" ", "seconds"))
    else:
        from os import linesep

        show_in_progress = args.date is None and args.range is None
        if show_in_progress:
            args.date = ["0"]
        try:
            entries = cli.get_entries_from_args(args)
        except argparse.ArgumentError as err:
            print(err)
            exit(1)

        if len(entries) > 0:
            if entries[0].begin.date() == entries[-1].begin.date():
                print(*text.ReportDetail(entries), sep=linesep)
            else:
                print(*text.ReportDaySummary(entries), sep=linesep)

        if show_in_progress:
            last = Entry.from_tsv(next(tsv.reverse_readline(args.tsv)))
            if last.begin.date() == datetime.date.today():
                print(
                    h_mm(datetime.datetime.now().astimezone() - last.cease),
                    "in progress ...",
                )


if __name__ == "__main__":
    main()
