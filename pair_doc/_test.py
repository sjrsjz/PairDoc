from .lexer import PairDocTokenizer, PairDocTokenType
from .ast import Gather, PairDocASTParser
from .html_builder import build_content, build_html
def test():
    test_doc = """
    ![func1 := (A:=1) -> {#A}];

    #func1()
    """
    tokenizer = PairDocTokenizer()
    tokens = tokenizer.parse(test_doc)

    gather = Gather(tokens)
    gathered = gather.gather()

    parser = PairDocASTParser(gathered)
    ast = parser.parse()
    print(ast)
    content = build_content(ast)
    print(content)
    html = build_html(content)

    with open('test.html', 'w', encoding='utf-8') as f:
        f.write(html)

if __name__ == "__main__":
    test()