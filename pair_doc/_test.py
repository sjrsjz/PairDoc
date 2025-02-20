from .lexer import PairDocTokenizer
from .ast import Gather, PairDocASTParser
from .html_builder import build_content, build_html
def test():
    test_doc = """
    #!var1 := "Hello" // This is a comment.

    #!var2 := "Word!" /* This is a block comment. */
    
    #!var2 = "World!"
    
    #h1{This is a test document.} #n
    
    #var1 #var2 #n

    #span['style="color:' + red + '"']{
        "This is a red text."
    }

    #---

    #!var3 := b{
        "This is a bold text."
    }
    #var3
    """


    tokenizer = PairDocTokenizer()
    tokens = tokenizer.parse(test_doc)

    gather = Gather(tokens)
    gathered = gather.gather()

    parser = PairDocASTParser(gathered)
    ast = parser.parse_doc()
    print(ast)
    content = build_content(ast)
    print(content)
    html = build_html(content)

    with open('test.html', 'w', encoding='utf-8') as f:
        f.write(html)

if __name__ == "__main__":
    test()