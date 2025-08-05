import re


class Replacer:
    def __init__(self, variables: dict):
        self.variables = variables

        self.patterns = {
            # !var!  - pastes variable as is (no recursion)
            'raw': re.compile(r'!([\w\.]+)!'),
            # $var$ - pastes variable with recursion (string)
            'recur_str': re.compile(r'\$([\w\.]+)\$'),
            # %var% - pastes variable with recursion as path (adds / and cleans)
            'recur_path': re.compile(r'%([\w\.]+)%'),
            # {var} - env variable
            'env': re.compile(r'\{(\w+)\}'),
        }

    # order is important to not change incorrect
    def replace(self, text: str, max_depth=10) -> str:
        import os

        def replace_env(m):
            key = m.group(1)
            return os.environ.get(key, m.group(0))

        text = self.patterns['env'].sub(replace_env, text)

        def replace_recur_str(s):
            for _ in range(max_depth):
                new_s = self.patterns['recur_str'].sub(
                    lambda m: str(self.variables.get(m.group(1), m.group(0))),
                    s
                )
                if new_s == s:
                    break
                s = new_s
            return s

        def replace_recur_path(s):
            for _ in range(max_depth):
                def repl(m):
                    val = self.variables.get(m.group(1))
                    if val is None:
                        return m.group(0)

                    start, end = m.start(), m.end()

                    before_slash = (start > 0 and s[start - 1] == os.sep)
                    after_slash = (end < len(s) and s[end] == os.sep)

                    if not before_slash:
                        val = os.sep + val
                    if not after_slash:
                        val = val + os.sep

                    return val

                new_s = self.patterns['recur_path'].sub(repl, s)
                if new_s == s:
                    break
                s = new_s

            if s.startswith('.'):
                prefix = '.'
                rest = s[1:]
                rest_norm = os.path.normpath(rest)
                final_path = prefix + rest_norm
            else:
                final_path = os.path.normpath(s)

            return final_path

        text = replace_recur_str(text)
        text = replace_recur_path(text)

        def replace_raw(m):
            key = m.group(1)
            return str(self.variables.get(key, m.group(0)))

        text = self.patterns['raw'].sub(replace_raw, text)

        return text
