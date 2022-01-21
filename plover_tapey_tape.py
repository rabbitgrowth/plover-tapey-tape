import itertools
import json
from datetime import datetime
from pathlib  import Path

import plover

class TapeyTape:
    SHOW_WHITESPACE = str.maketrans({'\n': '\\n', '\r': '\\r', '\t': '\\t'})

    @staticmethod
    def retroformat(translations):
        return ''.join(plover.formatting.RetroFormatter(translations).last_fragments(0))

    @staticmethod
    def show_action(action):
        if action.combo:
            return f'#{action.combo}'
        if action.command:
            return f'#{action.command}'
        # The assumption being that an Action can't contain combo/command
        # and text at the same time. You can define a stroke as, e.g.,
        # {#...}..., but that will get split into two Actions.
        if not action.text:
            return ''
        result = ''
        # To reduce visual clutter, don't show & and ^ at the same time
        if action.glue:
            result += '&'
        elif action.prev_attach:
            result += '^'
        result += action.text
        if action.next_attach:
            result += '^'
        return result

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
        self.old_actions        = None
        self.new_actions        = None
        self.was_fingerspelling = False

    def get_suggestions(self, translations):
        text = self.retroformat(translations)
        stroke_count = sum(len(translation.rtfcre) for translation in translations)
        return [outline
                for suggestion in self.engine.get_suggestions(text)
                for outline in suggestion.steno_list
                if len(outline) < stroke_count]

    def start(self):
        config_dir = Path(plover.oslayer.config.CONFIG_DIR)
        try:
            with config_dir.joinpath('tapey_tape.json').open() as f:
                config = json.load(f)
        except FileNotFoundError:
            config = {}

        self.debug_mode = bool(config.get('debug_mode'))

        try:
            # Set lower bound to some small non-zero number to avoid division by zero
            self.bar_time_unit = max(float(config['bar_time_unit']), 0.01)
        except (KeyError, ValueError):
            self.bar_time_unit = 0.2
        try:
            self.bar_max_width = min(max(int(config['bar_max_width']), 0), 100)
        except (KeyError, ValueError):
            self.bar_max_width = 5

        translation_style = config.get('translation_style')
        self.translation_style = ('dictionary'
                                  if translation_style not in ('mixed', 'minimal')
                                  else translation_style)

        # e.g., 1- -> S-, 2- -> T-, etc.
        self.numbers = {number: letter for letter, number in plover.system.NUMBERS.items()}

        self.engine.hook_connect('stroked',    self.on_stroked)
        self.engine.hook_connect('translated', self.on_translated)
        self.file = config_dir.joinpath('tapey_tape.txt').open('a')

    def stop(self):
        self.engine.hook_disconnect('stroked',    self.on_stroked)
        self.engine.hook_disconnect('translated', self.on_translated)
        self.file.close()

    def on_stroked(self, stroke):
        if self.debug_mode:
            self.file.write(f'{stroke}\n')

        # Translation stack
        translations = self.engine.translator_state.translations

        # Add back what was delayed
        if self.was_fingerspelling:
            # Maybe show suggestions
            if not stroke.is_correction and translations and not self.is_fingerspelling(translations[-1]):
                tail = list(reversed(list(itertools.takewhile(self.is_fingerspelling, reversed(translations[:-1])))))
                outlines = self.get_suggestions(tail)
                if outlines:
                    self.file.write('  >')
                self.file.write(' '.join(map('/'.join, outlines)))

            # Always add newline
            self.file.write('\n')

        # Bar
        now     = datetime.now()
        seconds = 0 if self.last_stroke_time is None else (now - self.last_stroke_time).total_seconds()
        width   = min(int(seconds / self.bar_time_unit), self.bar_max_width)
        bar     = ('+' * width).rjust(self.bar_max_width)
        if bar:
            self.file.write(bar)
            self.file.write(' ')
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
        self.file.write(f'|{steno}| ')

        # Star
        self.file.write('*' if self.old_actions else '')

        # If the stroke is an undo stroke, don't write anything more
        if stroke.is_correction or not translations:
            self.file.write('\n')
            self.file.flush()
            self.was_fingerspelling = False
            return

        # We can now rest assured that the translation stack is non-empty
        self.was_fingerspelling = self.is_fingerspelling(translations[-1])

        # Output
        if self.translation_style == 'mixed':
            output = ' '.join(filter(None, map(self.show_action, self.new_actions)))
        elif self.translation_style == 'minimal':
            output = self.retroformat(translations[-1:])
        else:
            definition = translations[-1].english
            output = '/' if definition is None else definition
            # TODO: don't show numbers as untranslate

        self.file.write(output.translate(self.SHOW_WHITESPACE))

        # Suggestions
        if not self.was_fingerspelling:
            suggestions = []
            for i in itertools.islice(reversed(range(len(translations))), 10):
                tail = translations[i:]
                # TODO: also show suggestion for, e.g., using KPA inefficiently
                if (self.is_whitespace(tail[-1])
                        or self.is_whitespace(tail[0])
                        or self.is_fingerspelling(tail[0])):
                    break
                outlines = self.get_suggestions(tail)
                if outlines:
                    suggestions.append('>' * len(tail) + ' '.join(map('/'.join, outlines)))
            if suggestions:
                self.file.write('  ')
            self.file.write(' '.join(suggestions))
            self.file.write('\n')

        self.file.flush()

    def on_translated(self, old_actions, new_actions):
        if self.debug_mode:
            self.file.write('\n')
            for prefix, actions in (('-', old_actions), ('+', new_actions)):
                for action in actions:
                    self.file.write(f'{prefix}{action}\n')

        self.old_actions = old_actions
        self.new_actions = new_actions
