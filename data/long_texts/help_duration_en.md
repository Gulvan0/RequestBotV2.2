Basic element of every duration is a **copula**. It has the following format: `<natural number><unit>`.  A copula represents a duration expressed in a single definite unit of time.

The available units are:
`s` - a second
`min` - a minute
`h` - an hour
`d` - a day
`w` - a week
`m` - 30 days
`q` - 90 days
`y` - 365 days

Examples of copula: `15d` - 15 days, `29min` - 29 minutes, `3y` - 3 years.

**Duration** can be absolute and relative.

**Absolute** duration consists of an arbitrary number of copulas, one after another without a space or a separator. The total length of its time interval is a sum of the durations of all the copulas comprising the absolute duration. For instance, `1q2m4d` - 154 days (5 months and 4 days), `1d5h12s` - 1 day 5 hours 12 seconds.

**Relative** duration is an absolute duration prepended with either a plus or a minus sign. For example, `+2w5d` - plus 19 days, `-3h` - minus 3 hours.

In some commands a choice between a relative and an absolute duration can affect the overall behaviour of the command quite significantly. For instance, when updating a cooldown specifying the absolute duration will set the duration of the cooldown to a given value. At the same time, specifying the relative duration will shift the current cooldown's end timestamp by a given amount.

Besides the absolute and relative duration there are also two special values:

- `0` - 0-second duration
- `inf` - infinite duration (used, for example, to specify and endless cooldown effectively banning a user or a level forever)