import json
import os
import plover
from datetime import datetime
from pathlib  import Path

class TapeyTape:
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

        try:
            # Set lower bound to some small non-zero number to avoid division by zero
            self.bar_time_unit = max(float(config['bar_time_unit']), 0.01)
        except (KeyError, ValueError):
            self.bar_time_unit = 0.2
        try:
            self.bar_max_width = min(max(int(config['bar_max_width']), 0), 100)
        except (KeyError, ValueError):
            self.bar_max_width = 5

        self.engine.hook_connect('stroked',    self.on_stroked)
        self.engine.hook_connect('translated', self.on_translated)
        self.file = config_dir.joinpath('tapey_tape.txt').open('a')

    def stop(self):
        self.engine.hook_disconnect('stroked',    self.on_stroked)
        self.engine.hook_disconnect('translated', self.on_translated)
        self.file.close()

    def on_stroked(self, stroke):
        now     = datetime.now()
        seconds = 0 if self.then is None else (now - self.then).total_seconds()
        width   = min(int(seconds / self.bar_time_unit), self.bar_max_width)
        bar     = ('+' * width).rjust(self.bar_max_width)
        space   = ' ' if bar else '' # so that setting width to 0 effectively hides the whole thing
        self.then = now

        keys  = set(stroke.steno_keys)
        steno = ''.join(key.strip('-') if key in keys else ' ' for key in plover.system.KEYS)
        stars = '*' * len(self.old)
        translation = ' '.join(action.text for action in self.new if action.text is not None)

        self.file.write(f'{bar}{space}|{steno}| {stars}{translation}\n')
        self.file.flush()

    def on_translated(self, old, new):
        self.old = old
        self.new = new
