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

if __name__ == '__main__':
    unittest.main()
