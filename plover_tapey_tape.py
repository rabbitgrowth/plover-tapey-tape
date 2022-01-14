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
        self.engine.hook_connect('stroked',    self.on_stroked)
        self.engine.hook_connect('translated', self.on_translated)
        self.file = Path(plover.oslayer.config.CONFIG_DIR).joinpath('tapey_tape.txt').open('a')

    def stop(self):
        self.engine.hook_disconnect('stroked',    self.on_stroked)
        self.engine.hook_disconnect('translated', self.on_translated)
        self.file.close()

    def on_stroked(self, stroke):
        now     = datetime.now()
        seconds = 0 if self.then is None else (now - self.then).total_seconds()
        width   = min(int(seconds / 0.2), 5)
        bar     = ('+' * width).rjust(5)
        self.then = now

        keys  = set(stroke.steno_keys)
        steno = ''.join(key.strip('-') if key in keys else ' ' for key in plover.system.KEYS)
        stars = '*' * len(self.old)
        translation = ' '.join(action.text for action in self.new if action.text is not None)

        self.file.write(f'{bar} |{steno}| {stars}{translation}\n')
        self.file.flush()

    def on_translated(self, old, new):
        self.old = old
        self.new = new
