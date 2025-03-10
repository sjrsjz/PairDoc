from .lexer import PairDocTokenizer, PairDocTokenType
import enum

class NextToken:
    # 用于获取下一个token list的类，自动匹配括号
    
    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0
    def next(self, start_idx:int):
        stack = []
        next_tokens = []
        if start_idx >= len(self.tokens):
            return next_tokens
        while True:
            if self.tokens[start_idx]['token'] in ('{', '[', '(') and self.tokens[start_idx]['type'] == PairDocTokenType.TokenType_SYMBOL:
                stack.append(self.tokens[start_idx]['token'])
                next_tokens.append(self.tokens[start_idx])
            elif self.tokens[start_idx]['token'] in ('}', ']', ')') and self.tokens[start_idx]['type'] == PairDocTokenType.TokenType_SYMBOL:
                if len(stack) == 0:
                    return next_tokens
                    #raise Exception('Unmatched bracket')
                poped = stack.pop()
                if (poped == '{' and self.tokens[start_idx]['token'] != '}') or \
                    (poped == '[' and self.tokens[start_idx]['token'] != ']') or \
                    (poped == '(' and self.tokens[start_idx]['token'] != ')'):
                    raise Exception('Unmatched bracket')
                
                next_tokens.append(self.tokens[start_idx])
            else:
                next_tokens.append(self.tokens[start_idx])
            start_idx += 1            
            if len(stack) == 0 or start_idx >= len(self.tokens):
                break
        return next_tokens
    
class Gather:
    # 将token list中的token按照括号匹配进行分组，方便后续处理
    def __init__(self, tokens):
        self.tokens = tokens
    def gather(self):
        gathered = []
        offset = 0
        while next_token := NextToken(self.tokens).next(offset):
            gathered.append(next_token)
            offset += len(next_token)
        return gathered

def _is_doc(token_list):
    if len(token_list) < 2:
        return False
    return token_list[0]['token'] == '{' and token_list[-1]['token'] == '}'

def _unwrap_doc(token_list):
    if len(token_list) < 2:
        return []
    return token_list[1:-1]

def _is_pair(token_list):
    if len(token_list) < 2:
        return False
    return token_list[0]['token'] == '[' and token_list[-1]['token'] == ']'

def _unwrap_pair(token_list):
    if len(token_list) < 2:
        return []
    return token_list[1:-1]
def _is_tuple(token_list):
    if len(token_list) < 2:
        return False
    return token_list[0]['token'] == '(' and token_list[-1]['token'] == ')'

def _unwrap_tuple(token_list):
    if len(token_list) < 2:
        return []
    return token_list[1:-1]

def _is_sharp(token_list):
    if len(token_list) != 1:
        return False
    return token_list[0]['token'] == '#' and token_list[0]['type'] == PairDocTokenType.TokenType_SYMBOL

def _is_exclamation(token_list):
    if len(token_list) != 1:
        return False
    return token_list[0]['token'] == '!' and token_list[0]['type'] == PairDocTokenType.TokenType_SYMBOL

def _is_let(token_list):
    if len(token_list) != 1:
        return False
    return token_list[0]['token'] == ':=' and token_list[0]['type'] == PairDocTokenType.TokenType_SYMBOL

def _is_assign(token_list):
    if len(token_list) != 1:
        return False
    return token_list[0]['token'] == '=' and token_list[0]['type'] == PairDocTokenType.TokenType_SYMBOL
def _concat(token_list):
    return ''.join([token['token'] for token in token_list])

def _is_to(token_list):
    if len(token_list) != 1:
        return False
    return token_list[0]['token'] == '->' and token_list[0]['type'] == PairDocTokenType.TokenType_SYMBOL

def _is_separator(token_list):
    if len(token_list) != 1:
        return False
    return token_list[0]['token'] == ';' and token_list[0]['type'] == PairDocTokenType.TokenType_SYMBOL
def _is_comma(token_list):
    if len(token_list) != 1:
        return False
    return token_list[0]['token'] == ',' and token_list[0]['type'] == PairDocTokenType.TokenType_SYMBOL
def _is_string(token_list):
    if len(token_list) != 1:
        return False
    return token_list[0]['type'] == PairDocTokenType.TokenType_STRING
def _is_number(token_list):
    if len(token_list) != 1:
        return False
    return token_list[0]['type'] == PairDocTokenType.TokenType_NUMBER
def _is_linebreak(token_list):
    if len(token_list) != 1:
        return False
    return token_list[0]['token'] == '---' and token_list[0]['type'] == PairDocTokenType.TokenType_SYMBOL

def _is_symbol(token_list, symbol):
    if len(token_list) != 1:
        return False
    return token_list[0]['token'] == symbol and token_list[0]['type'] == PairDocTokenType.TokenType_SYMBOL


class PairDocASTNodeTypes(enum.Enum):
    NONE = 0
    STYLE = 1
    TEXT = 2
    VARIABLE = 3
    UNFUNCTIONAL = 4
    LET = 5
    NEVERRETURN = 6
    DOC = 7
    ASSIGN = 8
    FUNCTIONDEF = 9
    SEPARATOR = 10
    FUNCTIONCALL = 11
    CONTENTCONTROL = 12
    OPERATION = 13
    TUPLE = 14
    KEYVAL = 15
    NUMBER = 16


class PairDocASTNode:
    def __init__(self, node_type: PairDocASTNodeTypes, children):
        self.node_type = node_type
        self.children = children

    def __str__(self):
        return f'{self.node_type.name} {self.children}'
    def __repr__(self):
        return self.__str__()

class NodeMatcher:
    def __init__(self):
        self.matchers = {}
        self.matcher_order = []
    
    def register(self, priority: int):
        """装饰器，用于注册匹配器并指定优先级"""
        def decorator(matcher_class):
            self.matchers[matcher_class.__name__] = matcher_class
            # 按优先级插入
            for i, (p, _) in enumerate(self.matcher_order):
                if priority > p:
                    self.matcher_order.insert(i, (priority, matcher_class.__name__))
                    break
            else:
                self.matcher_order.append((priority, matcher_class.__name__))
            return matcher_class
        return decorator
    
    def match(self, token_list, start_idx, skip_priority=None):
        """按优先级顺序尝试匹配"""

        if token_list is None or len(token_list) == 0:
            return PairDocASTNode(PairDocASTNodeTypes.NONE, None), 0
        for priority, matcher_name in self.matcher_order:
            if skip_priority is not None and priority >= skip_priority:
                continue
            matcher_class = self.matchers[matcher_name]
            matcher = matcher_class(token_list)
            node, offset = matcher.match(start_idx)
            if node:
                return node, offset
        return None, 0


node_matcher = NodeMatcher()

@node_matcher.register(priority=60)
class PairDocSeparator:
    # 匹配 ;
    def __init__(self, token_list):
        self.token_list = token_list
    def match(self, start_idx):
        # 后向匹配，先搜索分号
        offset = 0

        left = []
        separated = []
        last_offset = 0
        while start_idx + offset < len(self.token_list):
            if _is_separator(self.token_list[start_idx + offset]):
                node, node_offset = node_matcher.match(left, 0)
                if not node:
                    return None, 0
                if node_offset != len(left):
                    raise Exception("Invalid separator: Left side can't be fully matched: ", left)
                separated.append(node)
                left = []
                offset += 1
                last_offset = offset
            elif _is_sharp(self.token_list[start_idx + offset]):
                break # 遇到新的#，停止匹配
            else:
                left.append(self.token_list[start_idx + offset])
                offset += 1
        if len(separated) == 0:
            return None, 0
        node, node_offset = node_matcher.match(left, 0)
        if not node:
            return None, 0
        return PairDocASTNode(PairDocASTNodeTypes.SEPARATOR, separated + [node]), last_offset + node_offset

@node_matcher.register(priority=59)
class PairDocTuple:
    # 匹配 xxx, xxx, ...
    def __init__(self, token_list):
        self.token_list = token_list
    def match(self, start_idx):
        offset = 0

        left = []
        separated = []
        last_offset = 0
        while start_idx + offset < len(self.token_list):
            if _is_comma(self.token_list[start_idx + offset]):
                node, node_offset = node_matcher.match(left, 0)
                if not node:
                    return None, 0
                if node_offset != len(left):
                    raise Exception("Invalid tuple: Left side can't be fully matched: ", left)
                separated.append(node)
                left = []
                offset += 1
                last_offset = offset
            elif _is_sharp(self.token_list[start_idx + offset]):
                break # 遇到新的#，停止匹配
            else:
                left.append(self.token_list[start_idx + offset])
                offset += 1
        if len(separated) == 0:
            return None, 0
        node, node_offset = node_matcher.match(left, 0)
        if not node:
            return None, 0
        return PairDocASTNode(PairDocASTNodeTypes.TUPLE, separated + [node]), last_offset + node_offset


@node_matcher.register(priority=50)
class PairDocNeverReturn:
    # 匹配 !
    def __init__(self, token_list):
        self.token_list = token_list
    def match(self, start_idx):
        if not _is_exclamation(self.token_list[start_idx]):
            return None, 0
        guess, offset = node_matcher.match(self.token_list, start_idx + 1)
        if not guess:
            return None, 0
        return PairDocASTNode(PairDocASTNodeTypes.NEVERRETURN, guess), offset + 1


@node_matcher.register(priority=40)
class PairDocLet:
    # 匹配 xxx := xxx
    def __init__(self, token_list):
        self.token_list = token_list
    def match(self, start_idx):
        if start_idx + 2 >= len(self.token_list):
            return None, 0
        if not _is_let(self.token_list[start_idx+1]):
            return None, 0
        
        left = Gather(self.token_list[start_idx]).gather()

        right_guess, offset = node_matcher.match(self.token_list, start_idx + 2) # 尝试匹配右边的表达式
        if not right_guess:
            return None, 0
        
        left_node, left_offset = node_matcher.match(left, 0)
        if not left_node:
            return None, 0
        if left_offset != len(left):
            raise Exception("Invalid let: Left side can't be fully matched: ", left)
        right_node = right_guess
        return PairDocASTNode(PairDocASTNodeTypes.LET, [left_node, right_node]), offset + 2

@node_matcher.register(priority=30)
class PairDocAssign:
    # 匹配 xxx = xxx
    def __init__(self, token_list):
        self.token_list = token_list
    def match(self, start_idx):
        if start_idx + 2 >= len(self.token_list):
            return None, 0
        if not _is_assign(self.token_list[start_idx+1]):
            return None, 0
        
        left = Gather(self.token_list[start_idx]).gather()

        right_guess, offset = node_matcher.match(self.token_list, start_idx + 2) # 尝试匹配右边的表达式
        if not right_guess:
            return None, 0
        
        left_node, left_offset = node_matcher.match(left, 0)
        if not left_node:
            return None, 0
        if left_offset != len(left):
            raise Exception("Invalid assgin: Left side can't be fully matched: ", left)
        right_node = right_guess
        return PairDocASTNode(PairDocASTNodeTypes.ASSIGN, [left_node, right_node]), offset + 2


@node_matcher.register(priority=10)
class PairDocOperatorLevel1:
    # +, -
    def __init__(self, token_list):
        self.token_list = token_list
    def match(self, start_idx):
        # 后向匹配，先搜索+和-
        offset = 0

        left = []
        operation = None
        last_offset = 0
        while start_idx + offset < len(self.token_list):
            if _is_symbol(self.token_list[start_idx + offset], '+') or _is_symbol(self.token_list[start_idx + offset], '-'):
                node, node_offset = node_matcher.match(left, 0)
                if not node:
                    return None, 0
                if node_offset != len(left):
                    return None, 0
                operation = self.token_list[start_idx + offset][0]['token']
                offset += 1
                last_offset = offset
                left = node
                break
            elif _is_sharp(self.token_list[start_idx + offset]):
                break # 遇到新的#，停止匹配
            else:
                left.append(self.token_list[start_idx + offset])
                offset += 1
        if operation is None:
            return None, 0
        node, node_offset = node_matcher.match(self.token_list, last_offset + start_idx)
        if not node:
            return None, 0
        return PairDocASTNode(PairDocASTNodeTypes.OPERATION, [left, operation, node]), last_offset + node_offset


@node_matcher.register(priority=5)
class PairDocFunctionKeyVal:
    # 匹配 xxx: xxx
    def __init__(self, token_list):
        self.token_list = token_list
    def match(self, start_idx):
        if start_idx + 2 >= len(self.token_list):
            return None, 0
        if not _is_symbol(self.token_list[start_idx+1], ':'):
            return None, 0
        
        left = Gather(self.token_list[start_idx]).gather()

        right_guess, offset = node_matcher.match(self.token_list, start_idx + 2)

        left_node, left_offset = node_matcher.match(left, 0)
        if not left_node:
            return None, 0
        if left_offset != len(left):
            raise Exception("Invalid key value pair: Left side can't be fully matched: ", left)
        right_node = right_guess
        return PairDocASTNode(PairDocASTNodeTypes.KEYVAL, [left_node, right_node]), offset + 2

@node_matcher.register(priority=4)
class PairDocFunctionDef:
    # 匹配 (xxx) -> {xxx}
    def __init__(self, token_list):
        self.token_list = token_list
    def match(self, start_idx):
        if start_idx + 2 >= len(self.token_list):
            return None, 0
        if not _is_tuple(self.token_list[start_idx]) or not _is_to(self.token_list[start_idx+1]) or not _is_doc(self.token_list[start_idx+2]):
            return None, 0
        
        left_node, left_offset = node_matcher.match(Gather(_unwrap_tuple(self.token_list[start_idx])).gather(), 0)
        if not left_node:
            return None, 0
        right_node = PairDocASTParser(Gather(_unwrap_doc(self.token_list[start_idx+2])).gather()).parse_doc()
        if not right_node:
            return None, 0
        return PairDocASTNode(PairDocASTNodeTypes.FUNCTIONDEF, [left_node, right_node]), 3

@node_matcher.register(priority=4)
class PairDocStyle:
    # 匹配 xxx {...} 或 xxx [...] {...}
    def __init__(self, token_list):
        self.token_list = token_list
    def match(self, start_idx):
        if not (start_idx + 2 < len(self.token_list) and _is_pair(self.token_list[start_idx+1]) and _is_doc(self.token_list[start_idx+2])) and \
            not (start_idx + 1 < len(self.token_list) and _is_doc(self.token_list[start_idx+1])):
            return None, 0
        
        if _is_pair(self.token_list[start_idx+1]):
            left = Gather(self.token_list[start_idx]).gather()
            args = Gather(_unwrap_pair(self.token_list[start_idx+1])).gather()
            body = Gather(_unwrap_doc(self.token_list[start_idx+2])).gather()
            left_node, left_offset = node_matcher.match(left, 0)
            if not left_node:
                return None, 0
            if left_offset != len(left):
                raise Exception("Invalid style: Left side can't be fully matched: ", left)
            args_node, args_offset = node_matcher.match(args, 0)
            if not args_node:
                return None, 0
            if args_offset != len(args):
                raise Exception("Invalid style: Args can't be fully matched: ", args)
            body_node = PairDocASTParser(body).parse_doc()
            return PairDocASTNode(PairDocASTNodeTypes.STYLE, [left_node, args_node, body_node]), 3            
        else:
            left = Gather(self.token_list[start_idx]).gather()
            body = Gather(_unwrap_doc(self.token_list[start_idx+1])).gather()
            left_node, left_offset = node_matcher.match(left, 0)
            if not left_node:
                return None, 0
            if left_offset != len(left):
                raise Exception("Invalid style: Left side can't be fully matched: ", left)
            body_node = PairDocASTParser(body).parse_doc()
            return PairDocASTNode(PairDocASTNodeTypes.STYLE, [left_node, None, body_node]), 2

@node_matcher.register(priority=3)
class PairDocMemberAccess:
    """匹配成员访问操作：xxx[xxx] 和 xxx.xxx"""
    def __init__(self, token_list):
        self.token_list = token_list

    def match(self, start_idx):
        # 尝试匹配 [] 或 . 或 () 访问操作
        offset = 0
        access_points = []  # [(offset, type)] type: '[]' 或 '.'
        while start_idx + offset < len(self.token_list):
            if _is_pair(self.token_list[start_idx + offset]):
                access_points.append((offset, '[]'))
                offset += 1
            elif _is_symbol(self.token_list[start_idx + offset], '.'):
                access_points.append((offset, '.'))
                offset += 1
            elif _is_tuple(self.token_list[start_idx + offset]):
                access_points.append((offset, '()'))
                offset += 1
            elif _is_sharp(self.token_list[start_idx + offset]):
                break
            else:
                offset += 1

        if len(access_points) == 0 or access_points[0][0] == 0:  # 没有匹配到任何访问操作
            return None, 0
        
        # 寻找最长的有效匹配
        idx = 0
        while idx < len(access_points):
            test_node, test_offset = node_matcher.match(
                self.token_list[start_idx:start_idx + access_points[idx][0]], 
                0
            )
            if not test_node:
                return None, 0
            if test_offset < access_points[idx][0]:
                break
            idx += 1

        idx -= 1
        if idx < 0:
            return None, 0

        # 处理左侧表达式
        left = self.token_list[start_idx:start_idx + access_points[idx][0]]
        left_node, left_offset = node_matcher.match(left, 0)
        if not left_node or len(left) != left_offset:
            return None, 0

        access_type = access_points[idx][1]
        if access_type == '[]':
            # 处理索引访问
            index = Gather(_unwrap_pair(self.token_list[start_idx + access_points[idx][0]])).gather()
            index_node, index_offset = node_matcher.match(index, 0)
            if not index_node or index_offset != len(index):
                return None, 0
            right_node = index_node
        elif access_type == '()':
            # 处理函数调用
            args = Gather(_unwrap_tuple(self.token_list[start_idx + access_points[idx][0]])).gather()
            args_node, args_offset = node_matcher.match(args, 0)
            if not args_node or args_offset != len(args):
                return None, 0
            if args_node.node_type != PairDocASTNodeTypes.TUPLE:
                args_node = PairDocASTNode(PairDocASTNodeTypes.TUPLE, [args_node]) # 单个参数的情况
            right_node = args_node
        else:  # access_type == '.'
            # 处理属性访问
            right_node, right_offset = node_matcher.match(
                self.token_list, 
                start_idx + access_points[idx][0] + 1
            )
            if not right_node:
                return None, 0

        if access_type == '()':
            return PairDocASTNode(
                PairDocASTNodeTypes.FUNCTIONCALL, 
                [left_node, right_node]
            ), access_points[idx][0] + 1
        else:
            return (
                PairDocASTNode(
                    PairDocASTNodeTypes.OPERATION, 
                    [left_node, access_type, right_node]
                ),
                access_points[idx][0] + (1 if access_type in ('[]', ) else right_offset + 1)
            )
@node_matcher.register(priority=1)
class PairDocVariable:
    # 匹配变量
    def __init__(self, token_list):
        self.token_list = token_list
    def match(self, start_idx):
        if _is_tuple(self.token_list[start_idx]):
            node, offset = node_matcher.match(Gather(_unwrap_tuple(self.token_list[start_idx])).gather(), 0)
            if not node:
                return None, 0
            return node, 1
        if _is_doc(self.token_list[start_idx]):
            return PairDocASTParser(Gather(_unwrap_doc(self.token_list[start_idx])).gather()).parse(), 1
        if _is_string(self.token_list[start_idx]):
            return PairDocASTNode(PairDocASTNodeTypes.TEXT, _concat(self.token_list[start_idx])), 1
        if _is_number(self.token_list[start_idx]):
            return PairDocASTNode(PairDocASTNodeTypes.NUMBER, _concat(self.token_list[start_idx])), 1
        if _is_linebreak(self.token_list[start_idx]):
            return PairDocASTNode(PairDocASTNodeTypes.VARIABLE, "@linebreak"), 1
        return PairDocASTNode(PairDocASTNodeTypes.VARIABLE, _concat(self.token_list[start_idx])), 1



class PairDocASTParser:
    def __init__(self, token_list):
        self.token_list = token_list
        self.offset = 0
    def parse(self)->list: # 返回一个list，每个元素是一个PairDocASTNode
        ret = []

        not_doc = False
        while self.offset < len(self.token_list):
            if _is_sharp(self.token_list[self.offset]):
                not_doc = True
                self.offset += 1
                continue
            if not_doc:
                node, offset = node_matcher.match(self.token_list, self.offset)
                if node:
                    ret.append(node)
                    self.offset += offset
                else:
                    self.offset += 1
                not_doc = False
            else:
                if _is_doc(self.token_list[self.offset]):
                    ret.append(PairDocASTParser(Gather(_unwrap_doc(self.token_list[self.offset])).gather()).parse_doc())
                    self.offset += 1
                elif _is_pair(self.token_list[self.offset]):
                    ret.append(PairDocASTParser(Gather(_unwrap_pair(self.token_list[self.offset])).gather()).parse_doc())
                    self.offset += 1
                elif _is_tuple(self.token_list[self.offset]):
                    ret.append(PairDocASTParser(Gather(_unwrap_tuple(self.token_list[self.offset])).gather()).parse_doc())
                    self.offset += 1
                else:
                    ret.append(PairDocASTNode(PairDocASTNodeTypes.TEXT, _concat(self.token_list[self.offset])))
                    self.offset += 1
        return ret

    def parse_doc(self):
        return PairDocASTNode(PairDocASTNodeTypes.DOC, self.parse())
