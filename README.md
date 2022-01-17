# plover-tapey-tape

`plover-tapey-tape` is an alternative to Plover’s built-in paper tape.
It provides a side-by-side view of strokes and translations as well as
extra information such as bars to the left representing how long each
stroke took so that you can see which words you struggle with the most.

```
      |   KP   A              | {}{-|}
   ++ |      H AO*E  R     S  | here's
    + |     WH A              | what
      |  T                    | it
 ++++ |      HRAO      B G   Z| look {^s}
   ++ |      HRAO EU   B G    | like
    + |  T P H                | in
    + |    P  RA       B G S  | practice
    + |  T P          P L     | {.}
```

As you write, the paper tape is written in real time to a file named
`tapey_tape.txt` in Plover’s configuration directory:

- Windows: `%USERPROFILE%\AppData\Local\plover`
- macOS: `~/Library/Application Support/plover`
- Linux: `~/.config/plover`

You can review the file afterwards or use a tool like `tail -f` to
get a real-time feed.

## Activation

After you’ve installed this plugin, you have to enable it manually
by opening the main Plover window, going to Configure → Plugins, and
checking the box next to `plover-tapey-tape`.

## Configuration

If you want to customize the way the paper tape is displayed, you can
configure this plugin by creating a JSON file named `tapey_tape.json`
in Plover’s configuration directory (see above). The available options
are:

- `bar_time_unit`: The amount of time in seconds each `+` sign represents.
  Defaults to `0.2`.
- `bar_max_width`: The maximum number of `+` signs shown. Set this to `0`
  to hide the bars. Defaults to `5`.
- `translation_style`:
    - `minimal`: Only show characters that are actually output.
    - `mixed`: Also show “invisible” information like attachment (`^`),
      glue (`&`), and commands (`#`).
    - `dictionary`: Show the definitions in your dictionary. If a stroke
      is not defined, show `/`. This is the default.

```
                          minimal:  mixed:    dictionary (default):

|    P HR O       LG    |           #TOGGLE   {PLOVER:TOGGLE}
|    P H       R        | Mr.       Mr.       Mr.{-|}
|    PW R O  U  PB      | Brown     Brown     brown
|      H  O EU    L   DZ| HOEULDZ   HOEULDZ   /
|          *            | *         *         *
|      H  O E     L   DZ| holds     holds     holds
|        A  EU          | a         a         a
|    P     *    P       | P         &P        {&P}
|      H   *            | h         &h        {>}{&h}
|  TK      *    P       | D         &D        {&D}
|  TK       E      G    | degree    degree    degree
|  T P H                | in        in        in
|  T P H AO* U R        | neuro     neuro^    {neuro^}
| S K   RAO EU  PB   S  | science   ^science  science
|  T P          P L     | .         ^.        {.}
| S K W RA   U R B G S  |           ^\n\n^    {^\n\n^}{-|}
```

For example, to stretch out the bars to twice the default width and set
the translation style to `minimal`, use

```json
{
    "bar_time_unit": 0.1,
    "bar_max_width": 10,
    "translation_style": "minimal"
}
```
