from .ast import Gather, PairDocASTParser, PairDocASTNodeTypes, PairDocASTNode
import enum





class ContentTypes(enum.Enum):
    TEXT = 1
    STYLE = 2
    BLOCK = 3
    FUNCTION = 4


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
    
    def __str__(self):
        if isinstance(self.content, list):
            return f'{self.content_type} {str([str(c) for c in self.content])}'
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
        self.vars = []
    def let(self, key, value):
        for k, v in self.vars:
            if k == key:
                v.content = value.content.copy()
                return
        self.vars.append((key.copy(), value.copy()))

    def get(self, key):
        for k, v in self.vars:
            if k == key:
                return v
        if self.super_context:
            return self.super_context.get(key)
        return None
    
    def update(self, key, value):
        for k, v in self.vars:
            if k == key:
                v.content = value.content.copy()
                return
        if self.super_context:
            self.super_context.update(key, value)
        else:
            raise ValueError("Variable not found")

    def copy(self):
        new_context = Context(self.super_context)
        new_context.vars = [(k.copy(), v.copy()) for k, v in self.vars]
        return new_context

def _is_text(token:Content, text):
    return token.content_type == ContentTypes.BLOCK and len(token.content) == 1 and token.content[0].content_type == ContentTypes.TEXT and token.content[0].content == text
def _get_special_variable(token, context_vars:Context = None):
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
    
    raise ValueError("Unknown special token: " + str(token))

def _unwrap_block(content:Content):
    # 如果是块类型，那么解包并获得最后一个元素
    if isinstance(content, Content) and content.content_type == ContentTypes.BLOCK:
        return _unwrap_block(content.content[-1])
    return content
    

def build_content(ast:list, context_vars:Context = None, unfunctional = False)->str:
    if unfunctional:
        local_vars = context_vars
    else:
        local_vars = Context(context_vars)
    print(">>", ast)
    def _build(ast:PairDocASTNode):

        if ast.node_type == PairDocASTNodeTypes.STYLE:
            style, args, children = ast.children
            style = build_content(style, context_vars=local_vars)
            if args is not None:
                args = build_content(args, context_vars=local_vars)
            children = build_content(children, context_vars=local_vars)
            return Content(ContentTypes.STYLE, (style, args, children))

        if ast.node_type == PairDocASTNodeTypes.TEXT:
            return Content(ContentTypes.TEXT, ast.children)
        if ast.node_type == PairDocASTNodeTypes.SPECIAL:
            return _get_special_variable(build_content(ast.children, context_vars=local_vars), context_vars=local_vars)
        if ast.node_type == PairDocASTNodeTypes.UNFUNCTIONAL:
            return build_content(ast.children, context_vars=local_vars, unfunctional=True)
        if ast.node_type == PairDocASTNodeTypes.LET:
            key, value = ast.children
            k = build_content(key, context_vars=local_vars)
            v = build_content(value, context_vars=local_vars)
            local_vars.let(k, v)
            return v
        if ast.node_type == PairDocASTNodeTypes.NEVERRETURN:
            build_content(ast.children, context_vars=local_vars, unfunctional=True)
            return None
        if ast.node_type == PairDocASTNodeTypes.DOC:
            return build_content(ast.children, context_vars=local_vars)
        if ast.node_type == PairDocASTNodeTypes.ASSIGN:
            key, value = ast.children
            k = build_content(key, context_vars=local_vars)
            v = build_content(value, context_vars=local_vars)
            local_vars.update(k, v)
            return v
        if ast.node_type == PairDocASTNodeTypes.SEPARATOR:
            result = [build_content(c, context_vars=local_vars, unfunctional=True) for c in ast.children]
            return result[-1]
        if ast.node_type == PairDocASTNodeTypes.FUNCTIONDEF:
            args, body = ast.children
            context_copy = local_vars.copy()
            args = build_content(args, context_vars=context_copy) # TODO: 修正这里的逻辑
            return Content(ContentTypes.FUNCTION, [context_copy, args, body])
        if ast.node_type == PairDocASTNodeTypes.FUNCTIONCALL:
            func, args = ast.children
            func = _unwrap_block(build_content(func, context_vars=local_vars))
            if func.content_type != ContentTypes.FUNCTION:
                raise ValueError("Not a function")
            context, func_args, body = func.content
            args = build_content(args, context_vars=local_vars)
            #context.let(func_args, args)
            print(body)
            result = build_content(body, context_vars=context, unfunctional=True)
            print(result)
            return result
        raise ValueError("Unknown AST type")
    
    return Content(ContentTypes.BLOCK, [_build(node) for node in ast])

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
    raise ValueError("Unknown content type")
