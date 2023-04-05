import argparse
from pathlib import Path

from idid import cli, tsv, text as txt


def parsing() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    tsv = Path(__file__).parent / "data" / "idid.tsv"
    for k, v in cli.parser_options(tsv=tsv):
        parser.add_argument(k, **v)
    return parser


def test_get_day():
    args = parsing().parse_args("-d 2021-10-22 -x lunch".split())
    days, filters = cli.parse_entry_args(args)
    entries = tsv.get_entries(days, filters, tsv.reverse_readline(args.tsv, 64))
    assert 6 == len(entries)

    lines = txt.ReportDetail(entries)
    assert len(lines) == len(entries) + 3  # title, line, summary


def test_get_day_summary():
    args = parsing().parse_args("-d 2021-10-22 -x lunch".split())
    days, filters = cli.parse_entry_args(args)
    entries = tsv.get_entries(days, filters, tsv.reverse_readline(args.tsv, 64))
    assert 6 == len(entries)

    lines = txt.ReportDaySummary(entries)
    assert 2 == len(lines)
    assert lines[-1].endswith(" 8:19")
