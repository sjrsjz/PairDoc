from .ast import Gather, PairDocASTParser, PairDocASTNodeTypes, PairDocASTNode
import enum





class ContentTypes(enum.Enum):
    TEXT = 1
    STYLE = 2
    BLOCK = 3
    FUNCTION = 4
    TUPLE = 5
    KEYVALUE = 6
    INT = 7
    FLOAT = 8


class Content:
    def __init__(self, content_type, content):
        self.content_type = content_type
        if isinstance(content, list):
            self.content = content.copy()
        elif isinstance(content, dict):
            self.content = content.copy()
        else:
            self.content = content
    def __eq__(self, value):
        return self.content == value.content
    def __add__(self, value):
        if isinstance(self.content, list):
            self.content.append(value)
            return self
        if self.content_type == ContentTypes.TEXT and value.content_type == ContentTypes.TEXT:
            return Content(ContentTypes.TEXT, self.content + value.content)
        if self.content_type == ContentTypes.BLOCK:
            self.content.append(value)
            return self
        if self.content_type == ContentTypes.TUPLE:
            self.content.append(value)
            return self
        if self.content_type == ContentTypes.INT and value.content_type == ContentTypes.INT:
            return Content(ContentTypes.INT, self.content + value.content)
        raise ValueError("Cannot add")
    def __str__(self):
        return f'{self.content_type} {str(self.content)}'
    def __repr__(self):
        return self.__str__()
    
    def copy(self):
        return Content(self.content_type, self.content)

class Context:
    """
    上下文变量
    """
    def __init__(self, super_context=None):
        self.super_context = super_context
        self.vars = {}
    def let(self, key, value):
        self.vars[key] = value
    def update(self, key, value):
        if key in self.vars:
            self.vars[key] = value
        elif self.super_context is not None:
            self.super_context.update(key, value)
        else:
            raise ValueError("Variable not found")
    def get(self, key):
        if key in self.vars:
            return self.vars[key]
        if self.super_context is not None:
            return self.super_context.get(key)
        return None
    
    def copy(self):
        new_context = Context(self.super_context)
        new_context.vars = self.vars.copy()
        return new_context


def _is_text(token, text):
    return token == text
def _get_variable(token, context_vars:Context = None):
    v = context_vars.get(token)
    if v is not None:
        return v
    if _is_text(token, 'n') or _is_text(token, 'br'):
        return Content(ContentTypes.TEXT, '<br>')
    if _is_text(token, 't') or _is_text(token, 'tab'):
        return Content(ContentTypes.TEXT, '&nbsp;&nbsp;&nbsp;&nbsp;')
    if _is_text(token, 'q') or _is_text(token, 'quot'):
        return Content(ContentTypes.TEXT, '&quot;')
    if _is_text(token, 's'):
        return Content(ContentTypes.TEXT, '&nbsp;')
    if _is_text(token, '@linebreak'): # 分割线
        return Content(ContentTypes.TEXT, '<hr>')
    if _is_text(token, '$'):
        return context_vars.get('__args__')
    return Content(ContentTypes.TEXT, token)

def _unwrap_block(content:Content):
    # 如果是块类型，那么解包并获得最后一个元素
    if isinstance(content, Content) and content.content_type == ContentTypes.BLOCK:
        return _unwrap_block(content.content[-1])
    return content
    

def build_content(ast, context_vars:Context = None)->str:
    def _build(ast:PairDocASTNode):

        if ast.node_type == PairDocASTNodeTypes.STYLE:
            style, args, children = ast.children
            style = build_content(style, context_vars=context_vars)
            if args is not None:
                args = build_content(args, context_vars=context_vars)
            children = build_content(children, context_vars=context_vars)
            return Content(ContentTypes.STYLE, (style, args, children))

        if ast.node_type == PairDocASTNodeTypes.TEXT:
            return Content(ContentTypes.TEXT, ast.children)
        if ast.node_type == PairDocASTNodeTypes.NUMBER:
            if '.' in ast.children or 'e' in ast.children:
                return Content(ContentTypes.FLOAT, float(ast.children))
            else:
                return Content(ContentTypes.INT, int(ast.children))
        if ast.node_type == PairDocASTNodeTypes.VARIABLE:
            return _get_variable(ast.children, context_vars=context_vars)
        if ast.node_type == PairDocASTNodeTypes.UNFUNCTIONAL:
            return build_content(ast.children, context_vars=context_vars)
        if ast.node_type == PairDocASTNodeTypes.LET:
            key, value = ast.children
            if key.node_type != PairDocASTNodeTypes.VARIABLE:
                raise ValueError("Not a variable")
            k = key.children
            v = build_content(value, context_vars=context_vars)
            context_vars.let(k, v)
            return v
        if ast.node_type == PairDocASTNodeTypes.NEVERRETURN:
            build_content(ast.children, context_vars=context_vars)
            return None
        if ast.node_type == PairDocASTNodeTypes.DOC:
            new_context = Context(context_vars)
            doc_items = [build_content(c, context_vars=new_context) for c in ast.children]
            return Content(ContentTypes.BLOCK, doc_items)
        if ast.node_type == PairDocASTNodeTypes.ASSIGN:
            key, value = ast.children
            if key.node_type != PairDocASTNodeTypes.VARIABLE:
                raise ValueError("Not a variable")
            k = key.children
            v = build_content(value, context_vars=context_vars)
            context_vars.update(k, v)
            return v
        if ast.node_type == PairDocASTNodeTypes.SEPARATOR:
            result = [build_content(c, context_vars=context_vars) for c in ast.children]
            return result[-1]
        if ast.node_type == PairDocASTNodeTypes.FUNCTIONDEF:
            args, body = ast.children
            args = build_content(args, context_vars=context_vars)
            return Content(ContentTypes.FUNCTION, [context_vars, args, body])
        if ast.node_type == PairDocASTNodeTypes.FUNCTIONCALL:
            func, args = ast.children
            func = _unwrap_block(build_content(func, context_vars=context_vars))
            if func.content_type != ContentTypes.FUNCTION:
                raise ValueError("Not a function")
            
            args = build_content(args, context_vars=context_vars)
            #print(f"Executing function: <{func}> with {args}")

            context, func_args, body = func.content

            #遍历参数，将参数赋值，有两种情况，一种是直接赋值，一种是key-value赋值
            #先处理key-value赋值，然后将剩下的参数按顺序赋值
            key_values = [c for c in args.content if c.content_type == ContentTypes.KEYVALUE]
            non_key_values = [c for c in args.content if c.content_type != ContentTypes.KEYVALUE]

            arg_map = {x.content[0].content: x.content[1] for x in (func_args.content)}
            default_arg_map_is_used = {x.content[0].content: False for x in (func_args.content)}


            for kv in key_values:
                key, value = kv.content
                arg_map[key.content] = value
                if key.content in arg_map:
                    default_arg_map_is_used[key.content] = True
            for i, v in enumerate(non_key_values):
                if i >= len(func_args.content):
                    raise ValueError("Too many arguments")
                # 查找第一个未使用的默认参数
                for k, used in default_arg_map_is_used.items():
                    if not used:
                        arg_map[k] = v
                        default_arg_map_is_used[k] = True
                        break
                

            new_context = Context(context)
            for k, v in arg_map.items():
                new_context.let(k, v)

            result = build_content(body, context_vars=new_context)
            return result
        if ast.node_type == PairDocASTNodeTypes.OPERATION:
            left, op, right = ast.children
            left = build_content(left, context_vars=context_vars)
            right = build_content(right, context_vars=context_vars)
            if op == '+':
                return left + right
            if op == '-':
                return left - right
            if op == '[]':
                if left.content_type == ContentTypes.TUPLE:
                    return left.content[int(right.content)]
                if left.content_type == ContentTypes.TEXT:
                    return Content(ContentTypes.TEXT, left.content[int(right.content)])
                raise ValueError("Cannot use [] on non-tuple or non-text")
            if op == '.':
                if left.content_type == ContentTypes.TUPLE:
                    for c in left.content:
                        if not c.content_type == ContentTypes.KEYVALUE:
                            raise ValueError("Not a key-value pair")
                        if c.content[0].content == right.content:
                            return c.content[1]
                    raise ValueError("Key not found: " + right.content)
                if left.content_type == ContentTypes.KEYVALUE:
                    if right.content_type != ContentTypes.TEXT:
                        raise ValueError("Cannot use non-text key")
                    if right.content == 'key':
                        return left.content[0]
                    if right.content == 'value':
                        return left.content[1]
                    raise ValueError("Unknown key: " + right.content)
                if left.content_type == ContentTypes.TEXT:
                    if right.content_type != ContentTypes.INT:
                        raise ValueError("Cannot use non-number index for text")
                    return Content(ContentTypes.TEXT, left.content[int(right.content)])
                raise ValueError("Cannot use . on non-tuple or non-text")
            raise ValueError("Unknown operation: " + op)
        if ast.node_type == PairDocASTNodeTypes.TUPLE:
            result = [build_content(c, context_vars=context_vars) for c in ast.children]
            result = [c for c in result if c is not None] # 去掉None
            return Content(ContentTypes.TUPLE, result)
        if ast.node_type == PairDocASTNodeTypes.NONE:
            return None
        if ast.node_type == PairDocASTNodeTypes.KEYVAL:
            key, value = ast.children
            key = build_content(key, context_vars=context_vars)
            value = build_content(value, context_vars=context_vars)
            return Content(ContentTypes.KEYVALUE, [key, value])
        raise ValueError("Unknown AST type")
    
    return _build(ast)

def build_html(content:Content)->str:
    if content is None:
        return ''
    if content.content_type == ContentTypes.TEXT:
        return content.content
    if content.content_type == ContentTypes.STYLE:
        style, args, children = content.content
        style = build_html(style)
        children = build_html(children)
        if args is not None:
            args = build_html(args)
            return f'<{style} {args}>{children}</{style}>'
        return f'<{style}>{children}</{style}>'
    if content.content_type == ContentTypes.BLOCK:
        return ' '.join([build_html(c) for c in content.content])
    if content.content_type == ContentTypes.TUPLE:
        return "(" + ', '.join([build_html(c) for c in content.content]) + ")"
    if content.content_type == ContentTypes.KEYVALUE:
        key, value = content.content
        key = build_html(key)
        value = build_html(value)
        return f'{key}: {value}'
    if content.content_type == ContentTypes.INT:
        return str(content.content)
    if content.content_type == ContentTypes.FLOAT:
        return str(content.content)
    if content.content_type == ContentTypes.FUNCTION:
        context, args, body = content.content
        return f"{build_html(args)} -> {{{body}}}"
    raise ValueError("Unknown content type")
