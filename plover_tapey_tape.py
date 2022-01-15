import json
import plover
from datetime import datetime
from pathlib  import Path

class TapeyTape:
    @staticmethod
    def show_action(action):
        if action.combo:
            return f'#{action.combo}'
        if action.command:
            return f'#{action.command}'
        if not action.text:
            return None
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

    def __init__(self, engine):
        self.engine = engine
        self.then = None # time of the last stroke
        self.old  = None # actions undone
        self.new  = None # actions executed

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

        now     = datetime.now()
        seconds = 0 if self.then is None else (now - self.then).total_seconds()
        width   = min(int(seconds / self.bar_time_unit), self.bar_max_width)
        bar     = ('+' * width).rjust(self.bar_max_width)
        space   = ' ' if bar else '' # so that setting width to 0 effectively hides the whole thing
        self.then = now

        keys = set()
        for key in stroke.steno_keys:
            if key in self.numbers:                # e.g., if key is 1-
                keys.add(self.numbers[key])        #   add the corresponding S-
                keys.add(plover.system.NUMBER_KEY) #   and #
            else:                                  # if key is S-
                keys.add(key)                      #   add S-

        steno = ''.join(key.strip('-') if key in keys else ' ' for key in plover.system.KEYS)
        star  = '*' if self.old else ''
        translation = ' '.join(filter(None, map(self.show_action, self.new)))

        self.file.write(f'{bar}{space}|{steno}| {star}{translation}\n')
        self.file.flush()

    def on_translated(self, old, new):
        if self.debug_mode:
            self.file.write('\n')
            for prefix, actions in (('Old', old), ('New', new)):
                for action in actions:
                    self.file.write(f'{prefix}{action}\n')

        self.old = old
        self.new = new
