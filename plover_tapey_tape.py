import collections
import datetime
import json
import pathlib
import re

import plover

class TapeyTape:
    SHOW_WHITESPACE = str.maketrans({'\n': '\\n', '\r': '\\r', '\t': '\\t'})

    @staticmethod
    def retroformat(translations):
        return ''.join(plover.formatting.RetroFormatter(translations).last_fragments(0))

    @staticmethod
    def expand(format_string, items):
        def replace(match):
            width, letter = match.groups()
            width = 0 if not width else int(width)
            return items.get(letter, '').ljust(width)
        return re.sub('%(\d*)(.)', replace, format_string)

    @staticmethod
    def is_fingerspelling(translation):
        # For simplicity, just equate glue with fingerspelling for now
        return any(action.glue for action in translation.formatting)

    @staticmethod
    def is_whitespace(translation):
        return all(not action.text or action.text.isspace() for action in translation.formatting)

    def __init__(self, engine):
        self.engine = engine

        self.last_stroke_time   = None
        self.was_fingerspelling = False

    def get_suggestions(self, translations):
        text = self.retroformat(translations)
        stroke_count = sum(len(translation.rtfcre) for translation in translations)
        return [outline
                for suggestion in self.engine.get_suggestions(text)
                for outline in suggestion.steno_list
                if len(outline) < stroke_count]

    def start(self):
        # Config
        config_dir = pathlib.Path(plover.oslayer.config.CONFIG_DIR)
        try:
            with config_dir.joinpath('tapey_tape.json').open() as f:
                config = json.load(f)
        except FileNotFoundError:
            config = {}

        self.bar_character = config.get('bar_character', '+')
        if not isinstance(self.bar_character, str):
            raise TypeError('bar_character must be a string')

        bar_alignment = config.get('bar_alignment', 'right')
        if bar_alignment not in ('left', 'right'):
            raise ValueError('bar_alignment must be either "left" or "right"')
        self.bar_justifier = str.ljust if bar_alignment == 'left' else str.rjust

        # Be permissive with quoting. For example, just interpret
        #   "bar_time_unit": "0.5"
        # as
        #   "bar_time_unit": 0.5
        try:
            self.bar_time_unit = float(config.get('bar_time_unit', 0.2))
        except (TypeError, ValueError):
            raise TypeError('bar_time_unit must be a number')
        if self.bar_time_unit <= 0: # prevent division by zero
            raise ValueError('bar_time_unit must be a positive number')

        try:
            self.bar_max_width = int(config.get('bar_max_width', 5))
        except (TypeError, ValueError):
            raise TypeError('bar_max_width must be a number')

        line_format = config.get('line_format', '%b |%S| %D  %s')
        if not isinstance(line_format, str):
            raise TypeError('line_format must be a string')
        self.left_format, *rest = re.split(r'(\s*%s)', line_format, maxsplit=1)
        self.right_format = ''.join(rest)

        # e.g., 1- -> S-, 2- -> T-, etc.
        self.numbers = {number: letter for letter, number in plover.system.NUMBERS.items()}

        self.engine.hook_connect('stroked', self.on_stroked)

        self.file = config_dir.joinpath('tapey_tape.txt').open('a')

    def stop(self):
        if self.was_fingerspelling:
            self.file.write(self.expand(self.right_format, self.items).rstrip())
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
                    or self.is_fingerspelling(translations[-1])
                    or stroke.is_correction
                    or translations[-1].replaced):
                self.items['s'] = '' # suppress suggestions

            self.file.write(self.expand(self.right_format, self.items).rstrip())
            self.file.write('\n')

        # Bar
        now     = datetime.datetime.now()
        time    = now.isoformat(sep=' ', timespec='milliseconds')
        seconds = 0 if self.last_stroke_time is None else (now - self.last_stroke_time).total_seconds()
        width   = min(int(seconds / self.bar_time_unit), self.bar_max_width)
        bar     = self.bar_justifier(self.bar_character * width, self.bar_max_width)

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
            defined     = '*'
            translated  = '*'
            suggestions = ''
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
                defined = star + definition.translate(self.SHOW_WHITESPACE)
            # TODO: don't show numbers as untranslate

            formatted  = self.retroformat(translations[-1:])
            translated = star + formatted.translate(self.SHOW_WHITESPACE)

            # Suggestions
            suggestions = []

            if not self.is_whitespace(translations[-1]):
                buffer = []
                deque  = collections.deque()
                for translation in reversed(translations):
                    if self.is_fingerspelling(translation):
                        buffer.append(translation)
                    else:
                        if buffer:
                            deque.extendleft(buffer)
                            buffer = []
                            suggestions.append(self.get_suggestions(deque))
                        deque.appendleft(translation)
                        if not self.is_whitespace(translation):
                            suggestions.append(self.get_suggestions(deque))
                if buffer:
                    deque.extendleft(buffer)
                    suggestions.append(self.get_suggestions(deque))

            suggestions = ' '.join('>' * i + ' '.join(map('/'.join, outlines))
                                   for i, outlines in enumerate(suggestions, start=1)
                                   if outlines)

            self.was_fingerspelling = self.is_fingerspelling(translations[-1])

        self.items = {'t': time,
                      'b': bar,
                      'S': steno,
                      'r': raw_steno,
                      'D': defined,
                      'T': translated,
                      's': suggestions,
                      '%': '%'}

        self.file.write(self.expand(self.left_format, self.items))

        if not self.was_fingerspelling:
            self.file.write(self.expand(self.right_format, self.items).rstrip())
            self.file.write('\n')

        self.file.flush()
