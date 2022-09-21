import unittest

import plover_tapey_tape

from plover.formatting import _Action, Case

class MockTranslation:
    def __init__(self, rtfcre=(), english=None, formatting=None):
        self.rtfcre = rtfcre
        self.english = english
        self.formatting = formatting

T = MockTranslation
A = _Action

class TestTails(unittest.TestCase):
    def test_without_fingerspellings(self):
        translations = [
            T(english='hello', formatting=[A(text='Hello')]),
            T(english='world', formatting=[A(text='world')]),
            T(english='{.}',   formatting=[A(prev_attach=True, text='.')]),
        ]
        self.assertEqual(list(map(len, plover_tapey_tape.tails(translations))), [1, 2, 3])

    def test_with_fingerspellings(self):
        translations = [
            T(english='he',      formatting=[A(text='he')]),
            T(english='was',     formatting=[A(text='was')]),
            T(english='{>}{&k}', formatting=[A(next_case=Case.LOWER_FIRST_CHAR), A(glue=True, text='k')]),
            T(english='{>}{&v}', formatting=[A(glue=True, next_case=Case.LOWER_FIRST_CHAR), A(glue=True, prev_attach=True, text='v')]),
            T(english='{>}{&e}', formatting=[A(glue=True, next_case=Case.LOWER_FIRST_CHAR), A(glue=True, prev_attach=True, text='e')]),
            T(english='{>}{&t}', formatting=[A(glue=True, next_case=Case.LOWER_FIRST_CHAR), A(glue=True, prev_attach=True, text='t')]),
            T(english='{>}{&c}', formatting=[A(glue=True, next_case=Case.LOWER_FIRST_CHAR), A(glue=True, prev_attach=True, text='c')]),
            T(english='{>}{&h}', formatting=[A(glue=True, next_case=Case.LOWER_FIRST_CHAR), A(glue=True, prev_attach=True, text='h')]),
            T(english='{^ing}',  formatting=[A(prev_attach=True, text='ing')]),
            T(english='about',   formatting=[A(text='about')]),
            T(english='the',     formatting=[A(text='the')]),
            T(english='price',   formatting=[A(text='price')]),
            T(english='{.}',     formatting=[A(next_case=Case.LOWER_FIRST_CHAR, prev_attach=True, text='.')]),
        ]
        self.assertEqual(list(map(len, plover_tapey_tape.tails(translations))), [1, 2, 3, 4, 5, 11, 12, 13])

    def test_starts_with_fingerspellings(self):
        translations = [
            T(english='{&P}',    formatting=[A(glue=True, text='P')]),
            T(english='{>}{&h}', formatting=[A(glue=True, next_case=Case.LOWER_FIRST_CHAR), A(glue=True, prev_attach=True, text='h')]),
            T(english='{&D}',    formatting=[A(glue=True, prev_attach=True, text='D')]),
            T(english='degree',  formatting=[A(text='degree')]),
        ]
        self.assertEqual(list(map(len, plover_tapey_tape.tails(translations))), [1, 4])

class TestSuggestionKeys(unittest.TestCase):
    def test_attach(self):
        translations = [
            T(english='{^}', formatting=[A(prev_attach=True, next_attach=True, text='')]),
        ]
        self.assertEqual(plover_tapey_tape.suggestion_keys(translations), [])

    def test_affixes_in_definition(self):
        translations = [
            T(english='{pro^}',  formatting=[A(next_attach=True, text='pro')]),
            T(english='cure',    formatting=[A(prev_attach=True, text='cure')]),
            T(english='{^ment}', formatting=[A(prev_attach=True, text='ment')]),
        ]
        self.assertEqual(plover_tapey_tape.suggestion_keys(translations[:1]),  ['{pro^}',  'pro{^}'])
        self.assertEqual(plover_tapey_tape.suggestion_keys(translations[1:2]), ['cure'])
        self.assertEqual(plover_tapey_tape.suggestion_keys(translations[-1:]), ['{^ment}', '{^}ment'])
        self.assertEqual(plover_tapey_tape.suggestion_keys(translations[:2]),  ['procure'])
        self.assertEqual(plover_tapey_tape.suggestion_keys(translations[-2:]), ['curement'])
        self.assertEqual(plover_tapey_tape.suggestion_keys(translations),      ['procurement'])

    def test_affixes_with_attach(self):
        translations = [
            T(english='mid',  formatting=[A(text='mid')]),
            T(english='{^}',  formatting=[A(prev_attach=True, next_attach=True, text='')]),
            T(english='ship', formatting=[A(prev_attach=True, text='ship')]),
            T(english='{^}',  formatting=[A(prev_attach=True, next_attach=True, text='')]),
            T(english='man',  formatting=[A(prev_attach=True, text='man')]),
        ]
        self.assertEqual(plover_tapey_tape.suggestion_keys(translations[:2]),  ['{mid^}', 'mid{^}'])
        self.assertEqual(plover_tapey_tape.suggestion_keys(translations[1:4]), ['{^ship^}', '{^}ship{^}'])
        self.assertEqual(plover_tapey_tape.suggestion_keys(translations[-2:]), ['{^man}', '{^}man'])
        self.assertEqual(plover_tapey_tape.suggestion_keys(translations[:4]),  ['{midship^}', 'midship{^}'])
        self.assertEqual(plover_tapey_tape.suggestion_keys(translations[-4:]), ['{^shipman}', '{^}shipman'])
        self.assertEqual(plover_tapey_tape.suggestion_keys(translations[:1]),  ['mid'])
        self.assertEqual(plover_tapey_tape.suggestion_keys(translations[2:3]), ['ship'])
        self.assertEqual(plover_tapey_tape.suggestion_keys(translations[-1:]), ['man'])
        self.assertEqual(plover_tapey_tape.suggestion_keys(translations[:3]),  ['midship'])
        self.assertEqual(plover_tapey_tape.suggestion_keys(translations[-3:]), ['shipman'])
        self.assertEqual(plover_tapey_tape.suggestion_keys(translations),      ['midshipman'])

    def test_invalid_overbackspacing(self):
        translations = [
            T(english='united',           formatting=[A(text='united')]),
            T(english='states',           formatting=[A(text='states')]),
            T(english='{:retro_title:2}', formatting=[A(prev_attach=True, prev_replace='united states', text='United States')]),
        ]
        self.assertEqual(plover_tapey_tape.suggestion_keys(translations[-1:]), [])
        self.assertEqual(plover_tapey_tape.suggestion_keys(translations[-2:]), [])
        self.assertEqual(plover_tapey_tape.suggestion_keys(translations),      ['United States'])

    def test_valid_overbackspacing(self):
        translations = [
            T(english='smoke',  formatting=[A(text='smoke')]),
            T(english='{^ing}', formatting=[A(prev_attach=True, prev_replace='e', text='ing')]),
        ]
        self.assertEqual(plover_tapey_tape.suggestion_keys(translations[-1:]), ['{^ing}', '{^}ing'])
        self.assertEqual(plover_tapey_tape.suggestion_keys(translations),      ['smoking'])

if __name__ == '__main__':
    unittest.main()
