from .lexer import PairDocTokenizer
from .ast import Gather, PairDocASTParser
from .html_builder import build_content, build_html
def test():

    test_doc = """
    #!colored:=(color:black, text:'')->{
        #span['style="color:' + color + '"']{
            #text
        }
    }
    #!h1:=(text:'', color:'black')->{
        #'h1'{
            #colored(color, text)
        }
    }

    #h1('这是黑色的粗体标题')
    #---
    '''
    这是一段不会被解析的HTML，它可以写的很长很长 <br>

    而且可以加入任何的特殊字符，比如：#{}[]()等等 <br>
    '''
    #span['style="background-color:lightblue"']{
        '这是一段背景色为浅蓝色的文字'
    }
    #n // 换行

    /* 这是一段注释，不会被解析 */
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
            b:2,
            c:(
                (1, 2, 3),
                (4, 5, 6),
                (7, 8, 9)
            )
        )->{
            #a + b #n // 传入参数和表达式计算
            #c #n // 默认参数
            #object.B.C // 动态作用域引用父级变量
        }
    
    )

    #colored(object.method1(a:"原神", b:"启动"), color:'red')

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