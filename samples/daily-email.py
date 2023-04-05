#!/usr/bin/env python3
from collections import defaultdict
from datetime import date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from typing import List

from idid.tsv import Entries, get_entries
from idid.cli import make_date_range, parse_filters
from idid.entry import Entry, h_mm


_html_head: str = """<!DOCTYPE html>
<html>
<head lang="en-US">
    <title>{0}</title>
    <meta name="publisher" content="jidn/idid">
  <style>
    body { font-family: Calibri, Helvetica, sans-serif; }
    .idid { border-collapse: collapse; margin:0; min-width:400px; width:100% }
    .idid thead tr { background-color: #007cba; color: #ffffff; text-align: left; }
    .idid th,
    .idid td { padding: 6px 7px; }
    .idid td { vertical-align:top; }
    .idid tbody tr:nth-of-type(even){ background-color: #f3f3f3; }
    .idid tbody { border-bottom: 3px solid #007cba; }
    details summary { cursor: pointer; }
    summary { font-size:150% }
  </style>
</head><body>"""

_default_table: str = """<table class="idid">
<thead>
<tr>
    <th>Begin</th>
    <th>Cease</th>
    <th>Hours</th>
    <th>Description</th>
<tr>
</thead>
<tbody>"""


def _TR(*args) -> str:
    return "<tr><td>" + "</td><td>".join(args) + "</td></tr>"


def _detail_table_row(entries: Entries) -> List[str]:
    out = []
    for e in entries:
        out.append(
            _TR(
                e.begin.strftime("%H:%M"),
                e.cease.strftime("%H:%M"),
                h_mm(e.duration),
                e.text,
            )
        )
    return out


def HtmlDetail(entries: Entries, collapse: bool = True, show_total: bool = True) -> str:
    if len(entries) == 0:
        return ""
    out = []
    if collapse or show_total:
        total = sum((_.duration for _ in entries), timedelta())
        if collapse:
            title = entries[0].begin.strftime("%a %b %d, %Y")
            out.append(f"<details><summary>{title}  - {h_mm(total)}</summary>")
    out.append(_default_table)
    out.extend(_detail_table_row(entries))
    if show_total:
        out.append(_TR("", "", h_mm(total), "<b>TOTAL</b>"))
    out.append("</tbody></table>")
    if collapse:
        out.append("</details>")
    return "\n".join(out)


def ReportDaily(entries: List[Entry]) -> str:
    if len(entries) == 0:
        return ""

    entries.sort()
    last_day = entries[-1].begin.date()
    last_day_entries = [_ for _ in entries if _.begin.date() == last_day]

    out = [
        _html_head.replace("{0}", f"Daily Report {last_day.strftime('%a %b %d, %Y')}"),
        f"<h1>{last_day.strftime('%a %b %d, %Y')}</h1>",
    ]
    out.append(HtmlDetail(last_day_entries))
    out.append("</body></html>")
    return "\n".join(out)


def Report(entries: Entries) -> str:
    """Create report for each day."""
    dailies = defaultdict(list)
    grand_total = timedelta()
    for e in entries:
        dailies[e.begin.date()].append(e)
        grand_total += e.duration

    title = f"Report {entries[0].begin.strftime('%a %b %d, %Y')}"
    if entries[0].begin != entries[-1].begin:
        title += f" - {entries[-1].begin.strftime('%a %b %d, %Y')}"
    output = [
        _html_head.replace("{0}", title),
        f"<h2>Total hours - {h_mm(grand_total)}</h2>",
    ]
    days = sorted(dailies.keys(), reverse=True)
    # The latest day
    output.append(f"<h1>{days[0].strftime('%a %b %d, %Y')}</h1>")
    output.append(HtmlDetail(dailies[days[0]], collapse=False))
    for day in days[1:]:
        output.append(HtmlDetail(dailies[day]))
    output.append("</body></html>")
    return "\n".join(output)


def via_office365(mimemsg: MIMEMultipart, smtp_username, smtp_password):
    connection = smtplib.SMTP(host="smtp.office365.com", port=587)
    connection.starttls()
    connection.login(smtp_username, smtp_password)
    connection.send_message(mimemsg)
    connection.quit()


if __name__ == "__main__":
    from os import getenv

    entries = get_entries(
        [make_date_range("sun2", "today")], parse_filters("@personal", "")
    )
    mimemsg = MIMEMultipart()
    mimemsg["To"] = getenv("EMAIL_TO")
    mimemsg["From"] = getenv("EMAIL_FROM")
    mimemsg["Subject"] = f"Timesheet for {date.today().isoformat()}"
    mimemsg.attach(MIMEText(Report(entries), "html"))
    via_office365(mimemsg, getenv("SMTP_USERNAME"), getenv("SMTP_PASSWORD"))
