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
- `output_style`:
    - `defined`: Show translations as they are defined in your dictionary.
      If a stroke is not defined, show `/`. This is the default.
    - `translated`: Show translations as they are translated by Plover.
      In other words, only show characters that are actually output.

```
                          defined:  translated:

|    P H       R        | Mr.{-|}   Mr.
|    PW R O  U  PB      | brown     Brown
|      H  O EU    L   DZ| /         HOEULDZ
|          *            | *         *
|      H  O E     L   DZ| holds     holds
|        A  EU          | a         a
|    P     *    P       | {&P}      P
|      H   *            | {>}{&h}   h
|  TK      *    P       | {&D}      D
|  TK       E      G    | degree    degree
|  T P H                | in        in
|  T P H AO* U R        | {neuro^}  neuro
| S K   RAO EU  PB   S  | science   science
|  T P          P L     | {.}       .
```

For example, to stretch out the bars to twice the default width and set
the translation style to `translated`, use

```json
{
    "bar_time_unit": 0.1,
    "bar_max_width": 10,
    "output_style": "translated"
}
```

## Future plans

This plugin is under active development. The current priority is to
incorporate [clippy](https://github.com/tckmn/plover_clippy)-like
suggestions into the paper tape. (This is mostly motivated by a
personal desire to have all the information I need in a single window
when practicing.)

```
|   KP   A              | {}{-|}
|      H    E           | he
|             F      S  | was  >>EFS HEFS
|   K      *            | {>}{&k}
| S     R  *            | {>}{&v}
|          *E           | {>}{&e}
|  T       *            | {>}{&t}
|   K   R  *            | {>}{&c}
|      H   *            | {>}{&h}  >KW*EFP
|                  G    | {^ing}
|    PW                 | about
|                   T   | the  >>PW-T
|    P  RAO EU       S  | price
|  T P          P L     | {.}
```

In particular, I’m trying to make it treat fingerspelling as a special
case and only show suggestions for complete fingerspelled words
(for instance, `kvetch`, not sub-words like `vet`, `vetch`, `et`,
`etc`, `etch`, `etching`, `chin`, and `ching`).

## Acknowledgements

The name of this plugin is a tribute to
[Typey Type](https://didoesdigital.com/typey-type/),
a free resource for learning steno.

This plugin is heavily inspired by
[plover-clippy](https://github.com/tckmn/plover_clippy).
