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

You can customize the format of the output by creating a
[JSON](https://www.json.org/json-en.html) configuration file
named `tapey_tape.json` in Plover’s configuration directory
(see above). The available options are:

- `"bar_character"`: the character used to draw the hesitation bar.
  Defaults to `"+"`.
- `"bar_alignment"`: either `"left"` or `"right"` indicating whether the
  bar should be left-aligned or right-aligned. Defaults to `"right"`.
- `"bar_time_unit"`: the amount of time in seconds each character
  represents. Defaults to `0.2`.
- `"bar_max_width"`: the maximum number of characters drawn. Defaults to
  `5`.
- `"line_format"`: a string template specifying how each line in the
  output should be formatted. Special codes beginning with `%` are
  transformed into different items:

| Code | Item           | Example                                 |
|:-----|:---------------|:----------------------------------------|
| `%t` | date and time  | `2020-02-02 12:34:56.789`               |
| `%b` | hesitation bar | `+++++`                                 |
| `%S` | steno          | `...K.W.R....U.RPB......` (`.` = space) |
| `%r` | raw steno      | `KWRURPB`                               |
| `%D` | definition     | `yes{,}your Honor`                      |
| `%T` | translation    | `Yes, your Honor`                       |
| `%s` | suggestions    | `>>KWRURPB`                             |
| `%%` | an actual `%`  | `%`                                     |

The default format is `%b |%S| %D  %s`:

```
    %b |          %S           | %D      %s

  ++++ | ST        E   PB      | sten
    ++ | S K W R O             | *steno  >STOEUPB STO*EUPB
```

Here’s a comparison between `%D` and `%T`:

```
                          %D        %T

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

In short, `%D` is the *definition* in your dictionary, including
commands like `{-|}` and `{.}`. `%T` is the *translation* by Plover,
or the actual characters that are output. (If a stroke is undefined,
`%D` is displayed as `/`.)

You can additionally specify the *minimum width* of an item by inserting
a number between the `%` and the letter code. For example, `%10r` makes
the raw steno at least 10 characters wide by padding it with spaces.
This can be used to generate a tabular output:

```json
{
    "line_format": "%10r -> %T"
}
```

```
-T         -> The
KWEUBG     -> quick
PWROUPB    -> brown
TPOBGS     -> fox
SKWRUFRPZ  -> jumps
OEFR       -> over
-T         -> the
HRAEZ      -> lazy
TKOG       -> dog
TP-PL      -> .
```

Here’s an example `tapey_tape.json` that uses fancy Unicode symbols and
stretches the hesitation bar to twice its default width:

```json
{
    "bar_character": "░",
    "bar_time_unit": 0.1,
    "bar_max_width": 10,
    "line_format": "%b │%S│ %r → %T"
}
```

```
  ░░░░░░░░ │      H  O*E     L     │ HO*EL → Hello
     ░░░░░ │   K W          B G    │ KW-BG → ,
░░░░░░░░░░ │     W   O    R  L   D │ WORLD → world
       ░░░ │  T P           B G    │ TP-BG → !
```

Note that if you edit `tapey_tape.json` while Plover is running, you’ll
have to restart Plover for the new settings to take effect.

## Acknowledgements

The name of this plugin is a tribute to
[Typey Type](https://didoesdigital.com/typey-type/),
a free resource for learning steno.

This plugin is heavily inspired by
[plover-clippy](https://github.com/tckmn/plover_clippy).
