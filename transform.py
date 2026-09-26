import codecs

import sublime_plugin
from sublime_plugin import split_identifier


class Transformer(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        for s in view.sel():
            if s.empty():
                s = view.word(s)

            txt = self.transformer(view.substr(s))
            view.replace(edit, s, txt)


class SwapCaseCommand(Transformer):
    @staticmethod
    def transformer(s):
        return s.swapcase()


class UpperCaseCommand(Transformer):
    @staticmethod
    def transformer(s):
        return s.upper()


class LowerCaseCommand(Transformer):
    @staticmethod
    def transformer(s):
        return s.lower()


class TitleCaseCommand(Transformer):
    @staticmethod
    def transformer(s):
        return s.title()


class Rot13Command(Transformer):
    @staticmethod
    def transformer(s):
        return codecs.encode(s, 'rot-13')


def convert_case_function(option, preserve_abbreviations=True):
    return {
        'lower': str.lower,
        'upper': str.upper,
        # Title-case preserving abbreviations
        'title': lambda s: s if s.isupper() and preserve_abbreviations else s.capitalize(),
    }.get(option, lambda s: s)


class ConvertIdentCaseCommand(sublime_plugin.TextCommand):
    def run(self, edit, case, first_case=None, separator=''):
        case_f1 = convert_case_function(case)
        case_f2 = convert_case_function(case, False)

        if first_case is not None:
            first_case_f1 = convert_case_function(first_case)
            first_case_f2 = convert_case_function(first_case, False)
        else:
            first_case_f1 = case_f1
            first_case_f2 = case_f2

        view = self.view
        for sel in view.sel():
            if sel.empty():
                sel = view.word(sel)

            s = view.substr(sel).lstrip(' \t')
            # Don't preserve abbreviations if whole string is upper-case
            if s.isupper():
                txt = self._convert_case(s, separator, case_f2, first_case_f2)
            else:
                txt = self._convert_case(s, separator, case_f1, first_case_f1)

            view.replace(edit, sel, txt)

    def _convert_case(self, s, separator, case, first_case):
        return separator.join(
            first_case(part) if i == 0 else case(part)
            for i, part in enumerate(split_identifier(s)))
