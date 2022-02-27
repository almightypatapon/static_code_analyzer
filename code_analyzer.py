import re
import os
import sys
import ast


class CodeAnalyzer:

    errors_codes = {'S001': lambda f, i: f'{f}: Line {i}: S001 Too long',
                    'S002': lambda f, i: f'{f}: Line {i}: S002 Indentation is not a multiple of four',
                    'S003': lambda f, i: f'{f}: Line {i}: S003 Unnecessary semicolon after a statement',
                    'S004': lambda f, i: f'{f}: Line {i}: S004 At least two spaces required before inline comments',
                    'S005': lambda f, i: f'{f}: Line {i}: S005 TODO found',
                    'S006': lambda f, i: f'{f}: Line {i}: S006 More than two blank lines used before this line',
                    'S007': lambda f, i: f'{f}: Line {i}: S007 Too many spaces after construction',
                    'S008': lambda f, i: f'{f}: Line {i}: S008 Class name should be written in CamelCase',
                    'S009': lambda f, i: f'{f}: Line {i}: S009 Function name should be written in snake_case',
                    'S010': lambda f, i: f'{f}: Line {i}: S010 Argument name should be written in snake_case',
                    'S011': lambda f, i: f'{f}: Line {i}: S011 Variable in function should written in snake_case',
                    'S012': lambda f, i: f'{f}: Line {i}: S012 The default argument value is mutable'}

    def __init__(self):
        self.file = None
        self.lines = None
        self.tree = None
        self.issues = {}

    def read_file(self, path):
        self.file = path

        with open(self.file, 'r') as file:
            self.lines = file.readlines()
        with open(self.file, 'r') as file:
            self.tree = ast.parse(file.read())

    @staticmethod
    def is_snake_case(name):
        return re.match(r'[a-z_\d]+', name)
    
    def check_s001(self):
        for i, line in enumerate(self.lines):
            if len(line) > 79:
                self.issues.setdefault(i + 1, []).append('S001')

    def check_s002(self):
        for i, line in enumerate(self.lines):
            if not re.search(r'^( {4})+(\b|@)|^[^ ]', line):
                self.issues.setdefault(i + 1, []).append('S002')

    def check_s003(self):
        for i, line in enumerate(self.lines):
            if ';' in line and not re.search(r'''#.*;|['"].*;.*['"]''', line):
                self.issues.setdefault(i + 1, []).append('S003')

    def check_s004(self):
        for i, line in enumerate(self.lines):
            if '#' in line and not re.search(r'^#| {2}#', line):  # (?=((?<!^)#))(?=((?<! {2})#))
                self.issues.setdefault(i + 1, []).append('S004')

    def check_s005(self):
        for i, line in enumerate(self.lines):
            if re.search(r'#.*todo', line, re.IGNORECASE):
                self.issues.setdefault(i + 1, []).append('S005')

    def check_s006(self):
        counter = 0
        for i, line in enumerate(self.lines):
            if line == '\n':
                counter += 1
            else:
                if counter > 2:
                    self.issues.setdefault(i + 1, []).append('S006')
                counter = 0

    def check_s007(self):
        for i, line in enumerate(self.lines):
            if re.search(r'def[ ]{2}|class[ ]{2}', line):
                self.issues.setdefault(i + 1, []).append('S007')

    def check_s008(self):
        for i, line in enumerate(self.lines):
            if 'class' in line and not re.search(r'class +([A-Z]+[a-z]+)+[:|(]', line):
                self.issues.setdefault(i + 1, []).append('S008')

    def check_function(self):  # S009, S010, S011, S012
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                if not self.is_snake_case(node.name):  # S009
                    self.issues.setdefault(node.lineno, []).append('S009')
                for arg in node.args.args:
                    if not self.is_snake_case(arg.arg):  # S010
                        self.issues.setdefault(node.lineno, []).append('S010')
                for body in node.body:
                    if isinstance(body, ast.Assign):
                        for target in body.targets:
                            if isinstance(target, ast.Name) and not self.is_snake_case(target.id):  # S011
                                self.issues.setdefault(body.lineno, []).append('S011')
                for default in node.args.defaults:  # S012
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        self.issues.setdefault(node.lineno, []).append('S012')

    def check_all(self):
        self.check_s001()
        self.check_s002()
        self.check_s003()
        self.check_s004()
        self.check_s005()
        self.check_s006()
        self.check_s007()
        self.check_s008()
        self.check_function()

    def print_issues(self):
        for i in sorted(self.issues):
            for code in self.issues[i]:
                print(self.errors_codes[code](self.file, i))


class FilesAnalyzer(CodeAnalyzer):

    def __init__(self, path):
        super().__init__()
        path = path.lstrip('/')
        if path[-3:] == '.py':
            self.files = [path]
        else:
            self.files = sorted([f'{path}{os.sep}{file}' for file in os.listdir(f'{path}{os.sep}') if file[-3:] == '.py'])

    def analyze_all_files(self):
        for file in self.files:
            self.issues = {}
            self.read_file(file)
            self.check_all()
            self.print_issues()


if __name__ == '__main__':
    analyzer = FilesAnalyzer(sys.argv[-1])
    analyzer.analyze_all_files()
