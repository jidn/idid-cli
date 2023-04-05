# idid-cli

*idid-cli* is a simple command line tool for recording your accomplishment 
details into a tab separated file (TSV) and accessing those details.


[![PyPI - Version](https://img.shields.io/pypi/v/idid.svg)](https://pypi.org/jidn/idid-cli)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/idid.svg)](https://pypi.org/jidn/idid-cli)

-----

## Dev

```shell
$ python -m venv venv
$ activte
(venv)$ pip install -r requirements-dev
(venv)$ pip install --editable .
```

```shell
$ pip install -q build
$ python -m build
```

-----

**Table of Contents**

- [License](#license)
- [Quick Start](#Quick Start)
- [Installation](#installation)

## Installation

```shell
$ pip install --user idid-cli
```

## License

`idid-cli` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

## Quick Start

The idid model revolves around idea of recording what you just finished.
As you record your accomplishments, the duration is automatically keep.
If you need to adjust times, because you forgot to note when a meeting finished, alter the time and everything adjusts accordingly.

### Start your day
Your first accomplishment of the day is starting work.
You need a win, wherever you can find one.

```shell
$ idid -s -v
Thank you. It is now 07:55.
```

Wow, nice and polite. Without the `-v` verbose flag, it quitely records your time.

However, as I was coming in, Tim stopped me in the hall for about 10 minutes going over an item and it is now 8:05 am.
Altering the start time is easy. Just give it the number of minutes ago or the time.

```shell
$ idid -s 10 -v
Thank you. Starting at 07:55
$ idid -s 7:55 -v
Thank you. Starting at 07:55
```

### Additional accomplishments

As you finish a task or milestone, record what you did.

```shell
idid cleared inbox
Mon 08:20am  00:25  Well done!
```

Nice. I see the time, duration, and some positive feedback.

Later on, you forgot to record an accomplishment before talking to the team 10 minutes ago at 9:50.
To alter the time, use the `-t` option with either the number of minutes or the time.

```shell
$ idid -t 10 fixed issue #42
Mon 09:50  01:30  Well done!
```
or

```shell
$ idid -t 9:50 fixed issue #42
Mon 09:50  01:30  Well done!
```

Remember you are typing in your shell so there are some characters that will cause problems.
The most common issues are single quotes, semi colons and ampersands.
You will have to quote them or use natural language. 

### Edit your history

It is easy to add, but making modifications, insertions, and removing items increases the command line complexity.
My solution is not to create a bunch of command line parameters, but to use your favorite file editor.
If you are like me, and the vi family of editors is your friend, the following will open the TSV file in your editor and place you at the bottom, or most recent entry.

```shell
$ idid -e
```

Now you can make the changes you need.
Remove that double entry.
Add the accomplishment your forgot.
Fix the typos.
It is easier to correct in the editor than through a command-line tool.

Things to remember.

+ The TSV must be in chronological order. The duration is dependent on it.
+ There is no place for blank lines.
+ Do not alter the start text. See [Configuration](#Configuration) if you must change it.

### See your day

It would be nice to have a list of your accomplishments for today.
The date parameter `-d DATE` shows a list of all the days records.
`DATE` can be the words "today" or "yesterday".
It can also be the number of days in the past where zero means "today" and one means "yesterday".
So `-d today` and `-d 0` mean the same thing.

You can also use the abbreviated day-of-the-week for the last day.  
If today were Tuesday, `-d yesterday`, `-d 1`, and `-d mon` all give the same results.
Nice. Easy to find a way that works for you.

Need to get a date that is farther back?
I have you covered. Using the month and day as `MM-DD` or `MMDD`, will give you the results for that day.
While DATE as a number is difficult to use, any number less than a thousand is valid.
You can also use the day-of-the-week followed by a number for the number of weeks ago.

Here is an example. If today were 2022-08-01, the date of July 11th could be represented by any of the following.

+ `-d 0711`
+ `-d 07-11`
+ `-d 21` Twenty one days ago
+ `-d Mon4' Four Mondays ago

I know.  Seems a bit excessive. But I use them, so pick the one that works best for your need.
```
$ idid -d 0
```

### Lunch and extended breaks

In our previous example, lunch is shown as part of our day.
I want to remove it so the total hours matches the hours I was working. 
For some reason, those I report to don't want lunch included.

There are a two different strategies.
You can use `idid -s` after returning from lunch or extended break.
Now the time between your last entry and the start is not part of the record.

The other way is to exclude and entry from being selected.

### Exclude entries

You can exclude entries by comparing a [regular expression](https://en.wikipedia.org/wiki/Regular_expression) to the text.
Sounds scary but a simple text match will work for most cases and if you need the full power of regular expressions, I'll see you at the [regex golf course](https://alf.nu/RegexGolf).

In the previous section we didn't want to see our lunch break. 
Exclude entries using `-x REGEX` and for our case `-x "lunch"`.

```
$ idid -d 0 -x "lunch"
```

### Select entries

### Multiple days or date range

For multiple DATEs, use `-d DATE,DATE,...` using any valid DATE.
Go ahead and mix it up to your hearts content.

For range of dates, use the `-r DATE DATE/DAY` parameter.

