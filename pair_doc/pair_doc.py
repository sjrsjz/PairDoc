from .lexer import PairDocTokenizer
from .ast import Gather, PairDocASTParser
from .html_builder import build_content, build_html
def build_doc(doc):
    tokenizer = PairDocTokenizer()
    tokens = tokenizer.parse(doc)
    gather = Gather(tokens)
    gathered = gather.gather()
    parser = PairDocASTParser(gathered)
    ast = parser.parse_doc()
    content = build_content(ast)
    html = build_html(content)
    return html

