# plover-tapey-tape

`plover-tapey-tape` is an alternative to Plover’s built-in paper tape.
It provides a side-by-side view of strokes and translations as well as
some useful extra information.

```
      |   KP   A              | {}{-|}
   ++ |      H AO E  R        | here
    + |        A  E        S  | *here's  >HAO*ERS
    + |     WH A              | what
      |  T                    | it
 ++++ |      HRAO      B G   Z| look {^s}
   ++ |      HRAO EU   B G    | like
    + |  T P H                | in
    + |    P  RA       B G S  | practice
    + |  T P          P L     | {.}
```

The bars made up of `+`s on the left show the hesitation time for each
stroke so that you can see which words you struggle with the most.

The hints on the right beginning with `>` are
[clippy](https://github.com/tckmn/plover_clippy)-style suggestions
that show opportunities to write words or phrases more efficiently.
In the above example, it’s telling me that the two strokes I used for
“here’s”, `HAOER/AES`, can be condensed into one, `HAO*ERS`.

As you write, the paper tape is written in real time to a file named
`tapey_tape.txt` in Plover’s configuration directory:

- Windows: `%USERPROFILE%\AppData\Local\plover`
- macOS: `~/Library/Application Support/plover`
- Linux: `~/.config/plover`

You can review the file afterwards or use a tool like `tail -f` to
get a real-time feed.

## Fingerspelling

`tapey-tape` tries to be clever and treats contiguous fingerspelled
strokes as a group, so that when you
[fingerspell “kvetch”](https://www.youtube.com/watch?v=DIfjztBuBc8)
for example, it will only show suggestions for “kvetch”, not sub-words
like “vet”, “vetch”, “et”, “etc”, and “etch”.

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

## Installation

This plugin is not yet available in Plover’s plugins manager,
but for the time being, you should be able to install it with

```
plover -s plover_plugins install plover-tapey-tape
```

where `plover` stands for

- Windows: `C:\Program Files (x86)\Open Steno Project\Plover 4.0.0\plover_console.exe`
- macOS: `/Applications/Plover.app/Contents/MacOS/Plover`
- Linux: `plover.AppImage`

## Activation

After you’ve installed this plugin, you have to enable it manually
by opening the main Plover window, going to Configure → Plugins, and
checking the box next to `plover-tapey-tape`.

## Configuration

If you want to customize how things look, you can configure this plugin
by creating a JSON file named `tapey_tape.json` in Plover’s
configuration directory (see above). The available options are:

- `bar_time_unit`: the amount of time in seconds each `+` sign represents.
  Defaults to `0.2`.
- `bar_max_width`: the maximum number of `+` signs shown. Defaults to `5`.
- `line_format`: a string specifying exactly how each line in the paper
  tape should be formatted. `%` followed by another character has
  special meanings: `%b` means the bar, `%s` means the steno, `%o` means
  the output, and `%h` means suggestions (the “h” stands for “hint”).
  (If you want an actual `%` character, use `%%`.) The default format is
  `%b |%s| %o  %h`.
- `output_style`:
    - `definition`: Show what is defined in your dictionary. If a stroke
      is not defined, show `/`. This is the default.
    - `translation`: Show what is translated by Plover. In other words,
      only show characters that are actually output.

```
                          definition  translation:
                          (default):

|    P H       R        | Mr.{-|}     Mr.
|    PW R O  U  PB      | brown       Brown
|      H  O EU    L   DZ| /           HOEULDZ
|          *            | *           *
|      H  O E     L   DZ| holds       holds
|        A  EU          | a           a
|    P     *    P       | {&P}        P
|      H   *            | {>}{&h}     h
|  TK      *    P       | {&D}        D
|  TK       E      G    | degree      degree
|  T P H                | in          in
|  T P H AO* U R        | {neuro^}    neuro
| S K   RAO EU  PB   S  | science     science
|  T P          P L     | {.}         .
```

You need to follow the usual
[JSON rules](https://www.json.org/json-en.html)
like wrapping strings in double quotes. For example, to stretch out
the bars to twice the default width and set the output style to
`translation`, use

```json
{
    "bar_time_unit": 0.1,
    "bar_max_width": 10,
    "output_style": "translation"
}
```

```
  ++++++++ | ST        E   PB      | sten
      ++++ | S K W R O             | *steno  >STOEUPB STO*EUPB
```

To hide the bar and suggestions, use

```json
{
    "line_format": "|%s| %o"
}
```

```
| ST        E   PB      | sten
| S K W R O             | *steno
```

If you have a font that can display them, you can even use fancy
Unicode symbols like

```json
{
    "line_format": "│%s│ → %o"
}
```

```
│ ST        E   PB      │ → sten
│ S K W R O             │ → *steno
```

## Acknowledgements

The name of this plugin is a tribute to
[Typey Type](https://didoesdigital.com/typey-type/),
a free resource for learning steno.

This plugin is heavily inspired by
[plover-clippy](https://github.com/tckmn/plover_clippy).
