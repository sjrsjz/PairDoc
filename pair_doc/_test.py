from .lexer import PairDocTokenizer
from .ast import Gather, PairDocASTParser
from .html_builder import build_content, build_html
def test():
    test_doc = """
    #!var0 := b{我是奶龙}

    #var1 := (
        A:1,
        B:(
            C:span['style="color:orange"']{
                "我才是奶龙"
            },
            D:(114,514,1919810)
        )
    ) #n
    
    #var2 := var1.B #n

    #奶龙 := var0
    #var1[1].value.C #n

    #span['style="color:red"']{
        #"114514" 的第4位是 #b{#"114514".(3)}
    } #n

    #var1.B.D[2] #n

    #k_v := key1:("哦~", "今夜星光闪闪") #n
    k_v的键名是 #k_v.key #t
    k_v的键值是 #k_v.value

    '''
    <div style="color:orange">
        我才是奶龙
    </div>    
    '''

    #mat4x4 := (
        data: (
            (1, 2, 3, 4),
            (5, 6, 7, 8),
            (9, 10, 11, 12),
            (13, 14, 15, 16)
        ),
        dim: (4, 4)
    ) #n

    #mat4x4.("da" + "ta")[2][3]
    """

    test_doc = """
    #!object := (
        A:1,
        B:(
            C:span['style="color:orange"']{
                "我才是奶龙"
            },
            D:(114,514,1919810)
        ),
        method1:(
            a:1,
            b:2
        )->{
            #a + b
        }
    
    )

    #object.method1(1, 2)

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