import re


class Replacer:
    def __init__(self, variables: dict, original_variables: dict = None):
        self.variables = variables
        self.original_variables = original_variables or variables

        self.patterns = {
            # !var!  - pastes variable as is (no recursion)
            'raw': re.compile(r'!([\w\.\[\]]+)!'),
            # $var$ - pastes variable with recursion (string)
            'recur_str': re.compile(r'\$([\w\.\[\]]+)\$'),
            # %var% - pastes variable with recursion as path (adds / and cleans)
            'recur_path': re.compile(r'%([\w\.\[\]]+)%'),
            # {var} - env variable
            'env': re.compile(r'\{(\w+)\}'),
        }

    def replace(self, text: str, max_depth=10) -> str:
        import os

        def replace_env(m):
            key = m.group(1)
            return os.environ.get(key, m.group(0))

        def replace_recur_str(s):
            for _ in range(max_depth):
                def repl(m):
                    expr = m.group(1)
                    try:
                        return str(self.get_value_from_expr(expr))
                    except:
                        return m.group(0)

                new_s = self.patterns['recur_str'].sub(repl, s)
                if new_s == s:
                    break
                s = new_s
            return s

        def replace_recur_path(s):
            for _ in range(max_depth):
                def repl(m):
                    expr = m.group(1)
                    try:
                        resolved_val = self.get_value_from_expr(expr)

                        if isinstance(resolved_val, str):
                            resolved_val = replace_recur_str(resolved_val)
                        else:
                            resolved_val = str(resolved_val)

                        if not resolved_val.startswith(('.', os.sep)):
                            resolved_val = os.sep + resolved_val

                        if not resolved_val.endswith(os.sep):
                            resolved_val = resolved_val + os.sep

                        return resolved_val
                    except:
                        return m.group(0)

                new_s = self.patterns['recur_path'].sub(repl, s)
                if new_s == s:
                    break
                s = new_s

            if s.startswith('./') or s.startswith('.' + os.sep):
                prefix = './'
                rest = s[2:]
                rest_norm = os.path.normpath(rest)
                final_path = os.path.join(prefix, rest_norm)
            else:
                final_path = os.path.normpath(s)

            return final_path

        def replace_raw(m):
            expr = m.group(1)
            try:
                return str(self.get_value_from_expr(expr))
            except:
                return m.group(0)

        text = self.patterns['env'].sub(replace_env, text)
        text = replace_recur_str(text)
        text = replace_recur_path(text)
        text = self.patterns['raw'].sub(replace_raw, text)

        return text

    def get_value_from_expr(self, expr: str):
        import re

        # Split on dot first
        parts = expr.split('.')
        current = self.original_variables

        for part in parts:
            # Handle indexing, like model_weights[2]
            matches = re.finditer(r'([a-zA-Z_][\w\-]*)(\[\d+\])*', part)
            for match in matches:
                key = match.group(1)
                current = current[key]  # Go down one level
                indexes = re.findall(r'\[(\d+)\]', match.group(0))
                for idx in indexes:
                    current = current[int(idx)]
        return current

