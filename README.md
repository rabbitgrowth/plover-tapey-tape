# plover-tapey-tape

`plover-tapey-tape` is an alternative to Plover’s built-in paper tape.
It provides a side-by-side view of strokes and translations as well as
extra information such as bars to the left representing how long each
stroke took.

```
      |   KP   A              |
   ++ |      H AO*E  R     S  | Here's
    + |     WH A              | what
      |  T                    | it
 ++++ |      HRAO      B G   Z| looks
   ++ |      HRAO EU   B G    | like
    + |  T P H                | in
    + |    P  RA       B G S  | practice
    + |  T P          P L     | .
```

As you write, the paper tape is written in real time to a file named
`tapey_tape.txt` in Plover’s configuration directory:

- Windows: `%USERPROFILE%\AppData\Local\plover`
- macOS: `~/Library/Application Support/plover`
- Linux: `~/.config/plover`

You can review the file afterwards or use a tool like `tail -f` to
get a real-time feed.

## Configuration

To configure this plugin, create a JSON file named `tapey_tape.json`
in Plover’s configuration directory (see above). The available options
are as follows:

- `bar_time_unit`: The amount of time in seconds each `+` sign represents.
  Defaults to `0.2`.
- `bar_max_width`: The maximum number of `+` signs shown. Set this to `0`
  to hide the bar. Defaults to `5`.
