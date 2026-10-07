import re
from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont

class UniversalHighlighter(QSyntaxHighlighter):
    """High-performance multi-language syntax highlighter with pre-compiled regex tokens."""
    def __init__(self, document, file_extension=".py"):
        super().__init__(document)
        self.rules = []
        self.ext = file_extension.lower()
        self._init_formats()
        self._build_rules()

    def _init_formats(self):
        # VS Code Dark+ Theme Tokens
        self.fmt_keyword = QTextCharFormat()
        self.fmt_keyword.setForeground(QColor("#C586C0")) # Pink / Magenta
        self.fmt_keyword.setFontWeight(QFont.Bold)

        self.fmt_type = QTextCharFormat()
        self.fmt_type.setForeground(QColor("#4EC9B0")) # Teal

        self.fmt_builtin = QTextCharFormat()
        self.fmt_builtin.setForeground(QColor("#569CD6")) # Soft Blue

        self.fmt_func = QTextCharFormat()
        self.fmt_func.setForeground(QColor("#DCDCAA")) # Light Yellow

        self.fmt_string = QTextCharFormat()
        self.fmt_string.setForeground(QColor("#CE9178")) # Orange-Brown

        self.fmt_number = QTextCharFormat()
        self.fmt_number.setForeground(QColor("#B5CEA8")) # Light Green

        self.fmt_comment = QTextCharFormat()
        self.fmt_comment.setForeground(QColor("#6A9955")) # Green
        self.fmt_comment.setFontItalic(True)

        self.fmt_decorator = QTextCharFormat()
        self.fmt_decorator.setForeground(QColor("#DCDCAA"))

    def _build_rules(self):
        self.rules.clear()

        # Pre-compile number matching for speed
        self.rules.append((re.compile(r'\b[0-9]+(\.[0-9]+)?\b'), self.fmt_number))

        if self.ext in [".py"]:
            keywords = [
                r'\bdef\b', r'\bclass\b', r'\bimport\b', r'\bfrom\b', r'\breturn\b',
                r'\bif\b', r'\belif\b', r'\belse\b', r'\bwhile\b', r'\bfor\b',
                r'\btry\b', r'\bexcept\b', r'\bfinally\b', r'\bwith\b', r'\bas\b',
                r'\blambda\b', r'\byield\b', r'\braise\b', r'\bpass\b', r'\bglobal\b', r'\bnonlocal\b'
            ]
            builtins = [r'\bself\b', r'\bTrue\b', r'\bFalse\b', r'\bNone\b', r'\bprint\b', r'\blen\b', r'\brange\b', r'\bint\b', r'\bstr\b', r'\blist\b', r'\bdict\b']
            
            for kw in keywords: 
                self.rules.append((re.compile(kw), self.fmt_keyword))
            for b in builtins: 
                self.rules.append((re.compile(b), self.fmt_builtin))
                
            self.rules.append((re.compile(r'@[\w_]+'), self.fmt_decorator))
            self.rules.append((re.compile(r'\bdef\s+([a-zA-Z_][a-zA-Z0-9_]*)'), self.fmt_func))
            self.rules.append((re.compile(r'#.*$'), self.fmt_comment))
            self.rules.append((re.compile(r'".*?"|\'.*?\''), self.fmt_string))

        elif self.ext in [".cpp", ".c", ".h", ".hpp"]:
            keywords = [r'\bif\b', r'\belse\b', r'\bfor\b', r'\bwhile\b', r'\breturn\b', r'\bswitch\b', r'\bcase\b', r'\bbreak\b', r'\bnamespace\b', r'\busing\b']
            types = [r'\bint\b', r'\bfloat\b', r'\bdouble\b', r'\bchar\b', r'\bvoid\b', r'\bbool\b', r'\bauto\b', r'\bclass\b', r'\bstruct\b']
            
            for kw in keywords: self.rules.append((re.compile(kw), self.fmt_keyword))
            for t in types: self.rules.append((re.compile(t), self.fmt_type))
            self.rules.append((re.compile(r'#include\s+<.*?>|#include\s+".*?"'), self.fmt_string))
            self.rules.append((re.compile(r'//.*$'), self.fmt_comment))
            self.rules.append((re.compile(r'".*?"'), self.fmt_string))

        elif self.ext in [".js", ".ts", ".jsx", ".tsx"]:
            keywords = [r'\bfunction\b', r'\bconst\b', r'\blet\b', r'\bvar\b', r'\breturn\b', r'\bif\b', r'\belse\b', r'\bimport\b', r'\bfrom\b', r'\bexport\b', r'\basync\b', r'\bawait\b']
            for kw in keywords: self.rules.append((re.compile(kw), self.fmt_keyword))
            self.rules.append((re.compile(r'//.*$'), self.fmt_comment))
            self.rules.append((re.compile(r'".*?"|\'.*?\'|`.*?`'), self.fmt_string))

        elif self.ext in [".json"]:
            self.rules.append((re.compile(r'"(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(?=\s*:)'), self.fmt_builtin))
            self.rules.append((re.compile(r':\s*"(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"'), self.fmt_string))
            self.rules.append((re.compile(r'\btrue\b|\bfalse\b|\bnull\b'), self.fmt_keyword))

        elif self.ext in [".html", ".xml"]:
            self.rules.append((re.compile(r'</?[a-zA-Z0-9_]+'), self.fmt_builtin))
            self.rules.append((re.compile(r'>'), self.fmt_builtin))
            self.rules.append((re.compile(r'".*?"|\'.*?\''), self.fmt_string))
            self.rules.append((re.compile(r'<!--.*?-->'), self.fmt_comment))

    def highlightBlock(self, text):
        # Extremely fast execution using pre-compiled regex objects
        for regex, fmt in self.rules:
            for match in regex.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, fmt)