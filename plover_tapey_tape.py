#  ,-------.
# ( \       \    ~/steno $ tapeytape
#  `-|  'v'  |   [ T     A  EU  P  ] tape
#    |       |   [  K W RAO E      ] {^ey}
#    |  _____|   [     H        PB ] {^-^}
#    \ )      )  [ T     A  EU  P  ] tape
#     `-------'

import collections
import datetime
import json
import pathlib
import re

import plover

CONFIG_DIR = pathlib.Path(plover.oslayer.config.CONFIG_DIR)

SHOW_WHITESPACE = str.maketrans({'\n': '\\n', '\r': '\\r', '\t': '\\t'})

def make_absolute(filename):
    path = pathlib.Path(filename).expanduser()
    if not path.is_absolute():
        return CONFIG_DIR / path
    return path

def is_fingerspelling(translation):
    return any(action.glue for action in translation.formatting)

def is_whitespace(translation):
    return all(not action.text or action.text.isspace() for action in translation.formatting)

def is_retro(translation):
    return any(translation.english.startswith(start) for start in ('{*', '{:retro_', '=retrospective'))

def definition_starts_with_lowercase(translation):
    definition = translation.english
    return (definition
            and (definition[0].islower()
                 or (definition.startswith('{')
                     and definition.endswith('^}')
                     and definition[1].islower())
                 or (definition.startswith('{^')
                     and definition[2].islower())
                 or (definition.startswith('{^}')
                     and definition[3].islower())))

def tails(translations):
    assert translations
    if is_whitespace(translations[-1]) and not is_retro(translations[-1]):
        return
    tail = collections.deque()
    fingerspellings = []
    for translation in reversed(translations):
        if is_fingerspelling(translation):
            fingerspellings.append(translation)
        else:
            if fingerspellings:
                tail.extendleft(fingerspellings)
                fingerspellings = []
                yield tuple(tail)
            tail.appendleft(translation)
            yield tuple(tail)
    if fingerspellings:
        tail.extendleft(fingerspellings)
        yield tuple(tail)

def get_suggestion_keys(translations):
    assert translations
    actions = [action
               for translation in translations
               for action in translation.formatting]
    if not actions:
        return []
    output = ''
    last_action = None
    for action in actions:
        replace = len(action.prev_replace)
        if replace > len(output):
            return []
        if replace:
            output = output[:-replace]
        if (output
                and last_action is not None
                and action.text is not None
                and not action.prev_attach):
            output += action.space_char
        if action.text is not None:
            output += action.text
        if (last_action is None
                and output
                and output[0].isupper()
                and definition_starts_with_lowercase(translations[0])):
            output = output[0].lower() + output[1:]
        last_action = action
    if actions[0].prev_attach and actions[-1].next_attach:
        return [f'{{^{output}^}}', f'{{^}}{output}{{^}}']
    if actions[0].prev_attach:
        return [f'{{^{output}}}', f'{{^}}{output}']
    if actions[-1].next_attach:
        return [f'{{{output}^}}', f'{output}{{^}}']
    return [output]

def retroformat(translation):
    output = ''
    last_action = None
    for action in translation.formatting:
        replace = len(action.prev_replace)
        if replace:
            output = output[:-replace]
        if (output
                and last_action is not None
                and action.text is not None
                and not action.prev_attach):
            output += action.space_char
        if action.text is not None:
            output += action.text
        last_action = action
    return output

def expand(format_string, items):
    def replace(matchobj):
        width, letter = matchobj.groups()
        width = 0 if not width else int(width)
        return items.get(letter, '').ljust(width)
    return re.sub(r'%(\d*)(.)', replace, format_string)

class ConfigError(Exception):
    pass

class TapeyTape:
    def __init__(self, engine):
        self.engine = engine
        self.last_stroke_time = None
        self.was_fingerspelling = False

    def start(self):
        try:
            with (CONFIG_DIR / 'tapey_tape.json').open(encoding='utf-8') as f:
                config = json.load(f)
        except FileNotFoundError:
            config = {}
        else:
            if not isinstance(config, dict):
                raise ConfigError('Settings must be a JSON object')

        options = (
            ('output_file', str, lambda x: True, 'a string', 'tapey_tape.txt'),
            ('line_format', str, lambda x: True, 'a string', '%b |%S| %D  %s'),
            ('bar_character', str, lambda x: len(x) == 1, 'a 1-character string', '+'),
            ('bar_max_width', int, lambda x: True, 'an integer', 5),
            ('bar_time_unit', float, lambda x: x > 0, 'a positive number', 0.2),
            ('bar_threshold', float, lambda x: True, 'a number', 0.0),
            ('bar_alignment', str, lambda x: x in ('left', 'right'), 'either "left" or "right"', 'right'),
            ('suggestions_marker', str, lambda x: True, 'a string', '>'),
            ('dictionary_names', dict, lambda x: all(isinstance(k, str) and isinstance(v, str) for k, v in x.items()),
             'a JSON object mapping strings to strings', {}),
        )

        self.config = {}
        for option, type_, condition, description, default in options:
            try:
                value = config[option]
            except KeyError:
                value = default
            else:
                if not (isinstance(value, type_) and condition(value)):
                    raise ConfigError(f'{option} must be {description}')
            self.config[option] = value

        try:
            self.file = make_absolute(self.config['output_file']).open('a', encoding='utf-8')
        except OSError:
            raise ConfigError('output_file could not be opened')

        self.left_format, *rest = re.split(r'(\s*%s)', self.config['line_format'], maxsplit=1)
        self.right_format = ''.join(rest)

        self.dictionary_names = {str(make_absolute(filename)): name
                                 for filename, name in self.config['dictionary_names'].items()}

        # e.g., 1- -> S-, 2- -> T-, etc.
        self.numbers = {number: letter for letter, number in plover.system.NUMBERS.items()}

        self.engine.hook_connect('stroked', self.on_stroked)

    def stop(self):
        if self.was_fingerspelling:
            self.file.write(expand(self.right_format, self.items).rstrip())
            self.file.write('\n')

        self.engine.hook_disconnect('stroked', self.on_stroked)

        self.file.close()

    def on_stroked(self, stroke):
        # Do nothing if typing in QWERTY while Plover is off
        if not self.engine.output:
            return

        # Translation stack
        translations = self.engine.translator_state.translations

        # Add back what was delayed
        if self.was_fingerspelling:
            # Some important cases to consider in deciding whether to show suggestions:
            #
            # word &f &o &o word
            #   Stack: word
            #          word &f
            #          word &f &o
            #          word &f &o &o       (last)
            #          word &f &o &o word  (current)
            #   This is the most typical case. The last last-translation was fingerspelling,
            #   and the current last-translation is not, representing a turning point.
            #   Show suggestions for "foo" after the last &o.
            #
            # word &f &o &o word &b *
            #   Stack: word
            #          word &f
            #          word &f &o
            #          word &f &o &o
            #          word &f &o &o word
            #          word &f &o &o word &b
            #          word &f &o &o word
            #   Here it's also the case that the last last-translation was fingerspelling,
            #   and the current last-translation is not, representing a "turning point" --
            #   but not in the direction we want. If we don't handle these undo strokes
            #   specially, suggestions for "foo" would be shown after &b.
            #
            # Now, assume the user defines PW*/A*/R* as "BAR" in their dictionary.
            # Not sure why anyone would want to do something like that, but it's possible.
            #
            # word &f &o &o &b &a &r
            #   Stack: word
            #          word &f
            #          word &f &o
            #          word &f &o &o
            #          word &f &o &o &b
            #          word &f &o &o &b &a
            #          word &f &o &o BAR
            #   Again, this represents a "turning point" where we shouldn't show suggestions.
            #   If we don't handle this case specially, suggestions for "foo" would be shown
            #   after &a. We can identify this case by looking at whether anything got replaced
            #   in the current last-translation.
            if (not translations
                    or is_fingerspelling(translations[-1])
                    or stroke.is_correction
                    or translations[-1].replaced):
                self.items['s'] = '' # suppress suggestions

            self.file.write(expand(self.right_format, self.items).rstrip())
            self.file.write('\n')

        # Bar
        now  = datetime.datetime.now()
        time = now.isoformat(sep=' ', timespec='milliseconds')

        if self.last_stroke_time is None:
            bar = ' ' * self.config['bar_max_width']
        else:
            seconds = max((now - self.last_stroke_time).total_seconds() - self.config['bar_threshold'], 0)
            width   = min(int(seconds / self.config['bar_time_unit']), self.config['bar_max_width'])
            justify = str.ljust if self.config['bar_alignment'] == 'left' else str.rjust
            bar     = justify(self.config['bar_character'] * width, self.config['bar_max_width'])

        self.last_stroke_time = now

        # Steno
        keys = set()
        for key in stroke.steno_keys:
            if key in self.numbers:                # e.g., if key is 1-
                keys.add(self.numbers[key])        #   add the corresponding S-
                keys.add(plover.system.NUMBER_KEY) #   and #
            else:                                  # if key is S-
                keys.add(key)                      #   add S-
        steno = ''.join(key.strip('-') if key in keys else ' ' for key in plover.system.KEYS)
        raw_steno = stroke.rtfcre

        # At this point we start to deal with things for which we need to
        # examine the translation stack: output, suggestions, and determining
        # whether the current stroke is a fingerspelling stroke.

        if stroke.is_correction or not translations:
            # If the stroke is an undo stroke, just output * and call it a day.
            # (Sometimes it can be technically correct to show translations on
            # an undo stroke. For example:
            #   SPWOBGS +sandbox
            #   KAEUGS  -sandbox +intoxication
            #   *       -intoxication +sandbox
            # "sandbox" can be thought of as "translation" of the undo stroke.
            # But
            #   | S  PW   O      B G S  | sandbox
            #   |   K    A  EU     G S  | *intoxication
            #   |          *            | *sandbox
            # is probably not what the user expects.)
            defined         = '*'
            translated      = '*'
            dictionary_name = ''
            suggestions     = ''
            self.was_fingerspelling = False
        else:
            # We can now rest assured that the translation stack is non-empty.

            star = '*' if len(translations[-1].strokes) > 1 else ''
            # Here the * means something different: it doesn't mean that the
            # stroke is an undo stroke but that the translation is corrected.
            # (Note that Plover doesn't necessarily need to pop translations
            # from the stack to correct a translation. For example, there is
            # this (unnecessary) definition in main.json:
            #   "TP-PL/SO": "{.}so",
            # If you write TP-PL followed by SO, Plover just needs to push
            # "so" to the stack and doesn't need to pop {.}. Or maybe it does
            # pop {.}; it doesn't matter to us, because we can't see it from
            # the snapshots we get on stroked events anyway.)

            definition = translations[-1].english
            if definition is None:
                defined = '/'
            else:
                defined = star + definition.translate(SHOW_WHITESPACE)
            # TODO: don't show numbers as untranslate

            translated = star + retroformat(translations[-1]).translate(SHOW_WHITESPACE)

            # Dictionary name
            for dictionary in self.engine.dictionaries.dicts:
                if translations[-1].rtfcre in dictionary:
                    dictionary_name = self.dictionary_names.get(dictionary.path, '')
                    break
            else:
                dictionary_name = ''

            # Suggestions
            chunks = []
            for i, tail in enumerate(tails(translations), start=1):
                total_strokes = sum(len(translation.rtfcre) for translation in tail)
                outlines = ['/'.join(outline)
                            for suggestion_key in get_suggestion_keys(tail)
                            for outline in self.engine.dictionaries.reverse_lookup(suggestion_key)
                            if len(outline) < total_strokes]
                if outlines:
                    prefix = '' if i == 1 else str(i)
                    chunks.append(prefix + self.config['suggestions_marker'] + ' '.join(outlines))
                if i == 10:
                    break
            suggestions = ' '.join(chunks)

            self.was_fingerspelling = is_fingerspelling(translations[-1])

        self.items = {'t': time,
                      'b': bar,
                      'S': steno,
                      'r': raw_steno,
                      'D': defined,
                      'T': translated,
                      'd': dictionary_name,
                      's': suggestions,
                      '%': '%'}

        self.file.write(expand(self.left_format, self.items))

        if not self.was_fingerspelling:
            self.file.write(expand(self.right_format, self.items).rstrip())
            self.file.write('\n')

        self.file.flush()
