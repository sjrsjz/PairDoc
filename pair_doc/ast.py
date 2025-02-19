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

class PairDocASTNodeTypes(enum.Enum):
    STYLE = 1
    TEXT = 2
    SPECIAL = 3
    UNFUNCTIONAL = 4
    LET = 5
    NEVERRETURN = 6
    DOC = 7
    ASSIGN = 8
    FUNCTIONDEF = 9
    SEPARATOR = 10
    FUNCTIONCALL = 11


class PairDocASTNode:
    def __init__(self, node_type: PairDocASTNodeTypes, children):
        self.node_type = node_type
        self.children = children

    def __str__(self):
        return f'{self.node_type} {self.children}'
    def __repr__(self):
        return self.__str__()


class PairDocStyle:
    # 匹配 #style{...} 或者 #style[...]{...} 的样式
    def __init__(self, token_list):
        self.token_list = token_list

    def match(self, start_idx:int)->tuple:
        if start_idx + 2 >= len(self.token_list):
            return None, 0
        if not _is_sharp(self.token_list[start_idx]):
            return None, 0
        if _is_doc(self.token_list[start_idx+2]):
            style = Gather(self.token_list[start_idx+1]).gather()
            gathered = Gather(_unwrap_doc(self.token_list[start_idx+2])).gather()
            return PairDocASTNode(PairDocASTNodeTypes.STYLE, (PairDocASTParser(style).parse(), None, PairDocASTParser(gathered).parse())), 3
        if _is_pair(self.token_list[start_idx+2]) and start_idx + 3 < len(self.token_list) and _is_doc(self.token_list[start_idx+3]):
            style = Gather(self.token_list[start_idx+1]).gather()
            args = Gather(_unwrap_pair(self.token_list[start_idx+2])).gather()
            gathered = Gather(_unwrap_doc(self.token_list[start_idx+3])).gather()
            return PairDocASTNode(PairDocASTNodeTypes.STYLE, (PairDocASTParser(style).parse(), PairDocASTParser(args).parse(), PairDocASTParser(gathered).parse())), 4
        return None, 0

class PairDocSpecial:
    # 匹配 #special 的特殊样式
    def __init__(self, token_list):
        self.token_list = token_list
    def match(self, start_idx:int)->tuple:
        if start_idx + 1>= len(self.token_list):
            return None, 0
        if not _is_sharp(self.token_list[start_idx]):
            return None, 0
        tokens = Gather(self.token_list[start_idx+1]).gather()
        return PairDocASTNode(PairDocASTNodeTypes.SPECIAL, PairDocASTParser(tokens).parse()), 2

class PairDocUnFunctional:
    # 匹配 #func(...) 的函数调用
    def __init__(self, token_list):
        self.token_list = token_list
    def match(self, start_idx:int)->tuple:
        if start_idx >= len(self.token_list):
            return None, 0
        if not _is_pair(self.token_list[start_idx]):
            return None, 0
        inside = Gather(_unwrap_pair(self.token_list[start_idx])).gather()
        return PairDocASTNode(PairDocASTNodeTypes.UNFUNCTIONAL, PairDocASTParser(inside).parse()), 1

class PairDocASTFunctionDef:
    # 匹配 (...)->... 的函数类型
    def __init__(self, token_list):
        self.token_list = token_list
    def match(self, start_idx:int)->tuple:
        if start_idx + 2 >= len(self.token_list):
            return None, 0
        if not _is_to(self.token_list[start_idx+1]):
            return None, 0
        if not _is_tuple(self.token_list[start_idx]):
            return None, 0
        args = Gather(_unwrap_tuple(self.token_list[start_idx])).gather()
        right = Gather(self.token_list[start_idx+2]).gather()
        return PairDocASTNode(PairDocASTNodeTypes.FUNCTIONDEF, (PairDocASTParser(args).parse(), PairDocASTParser(right).parse())), 3
  

class PairDocASTLet:
    # 匹配 var:=... 的赋值
    def __init__(self, token_list):
        self.token_list = token_list
    def match(self, start_idx:int)->tuple:
        if start_idx + 2 >= len(self.token_list):
            return None, 0
        if not _is_let(self.token_list[start_idx+1]):
            return None, 0
        left = Gather(self.token_list[start_idx]).gather()
        right = self.token_list[start_idx+2:]
        return PairDocASTNode(PairDocASTNodeTypes.LET, (PairDocASTParser(left).parse(), PairDocASTParser(right).parse())), len(self.token_list) - start_idx

class PairDocASTAssign:
    # 匹配 var=... 的赋值
    def __init__(self, token_list):
        self.token_list = token_list
    def match(self, start_idx:int)->tuple:
        if start_idx + 2 >= len(self.token_list):
            return None, 0
        if not _is_assign(self.token_list[start_idx+1]):
            return None, 0
        left = Gather(self.token_list[start_idx]).gather()
        right = self.token_list[start_idx+2:]
        return PairDocASTNode(PairDocASTNodeTypes.ASSIGN, (PairDocASTParser(left).parse(), PairDocASTParser(right).parse())), len(self.token_list) - start_idx

class PairDocASTSubDocument:
    # 匹配 {...} 的子文档
    def __init__(self, token_list):
        self.token_list = token_list
    def match(self, start_idx:int)->tuple:
        if start_idx >= len(self.token_list):
            return None, 0
        if not _is_doc(self.token_list[start_idx]):
            return None, 0
        tokens = Gather(_unwrap_doc(self.token_list[start_idx])).gather()
        return PairDocASTNode(PairDocASTNodeTypes.DOC, PairDocASTParser(tokens).parse()), 1
class PairDocASTNeverReturn:
    # 匹配 !... ，区别是实际上不会返回值
    def __init__(self, token_list):
        self.token_list = token_list
    def match(self, start_idx:int)->tuple:
        if start_idx >= len(self.token_list):
            return None, 0
        if not _is_exclamation(self.token_list[start_idx]):
            return None, 0
        if start_idx + 1 >= len(self.token_list):
            return None, 0
        tokens = Gather(self.token_list[start_idx + 1]).gather()
        return PairDocASTNode(PairDocASTNodeTypes.NEVERRETURN, PairDocASTParser(tokens).parse()), 2

class PairDocASTSeparator:
    # 匹配 ...;... 的分隔符
    def __init__(self, token_list):
        self.token_list = token_list
    def match(self, start_idx:int)->tuple:
        # 遍历
        offset = 0
        separated = []
        tmp = []
        while start_idx + offset < len(self.token_list):
            if _is_separator(self.token_list[start_idx + offset]):
                separated.append(tmp)
                tmp = []
            else:
                tmp.append(self.token_list[start_idx + offset])
            offset += 1
        separated.append(tmp)

        if len(separated) == 1:
            return None, 0
        
        return PairDocASTNode(PairDocASTNodeTypes.SEPARATOR, [PairDocASTParser(tokens).parse() for tokens in separated]), len(self.token_list) - start_idx

class PairDocASTOrderChange:
    # 匹配 #(...)
    def __init__(self, token_list):
        self.token_list = token_list
    def match(self, start_idx:int)->tuple:
        if start_idx + 1>= len(self.token_list):
            return None, 0
        if not _is_sharp(self.token_list[start_idx]):
            return None, 0
        if not _is_tuple(self.token_list[start_idx + 1]):
            return None, 0
        
        gathered = Gather(_unwrap_tuple(self.token_list[start_idx + 1])).gather()

        return PairDocASTNode(PairDocASTNodeTypes.SEPARATOR, [PairDocASTParser(gathered).parse()]), 1

class PairDocASTFunctionCall:
    # 匹配 func(...) 的函数调用
    def __init__(self, token_list):
        self.token_list = token_list
    def match(self, start_idx:int)->tuple:
        if start_idx + 2 >= len(self.token_list):
            return None, 0
        if not _is_tuple(self.token_list[-1]):
            return None, 0
        func = self.token_list[0:-1]
        args = Gather(_unwrap_tuple(self.token_list[-1])).gather()
        return PairDocASTNode(PairDocASTNodeTypes.FUNCTIONCALL, (PairDocASTParser(func).parse(), PairDocASTParser(args).parse())), len(self.token_list) - start_idx

class PairDocASTParser:
    def __init__(self, token_list):
        self.token_list = token_list
        self.offset = 0
    def parse(self, unfunctional = False)->list: # 返回一个list，每个元素是一个PairDocASTNode
        ret = []
        while self.offset < len(self.token_list):
            sep, offset = PairDocASTSeparator(self.token_list).match(self.offset)
            if sep:
                ret.append(sep)
                self.offset += offset
                continue
            style, offset = PairDocStyle(self.token_list).match(self.offset)
            if style:
                ret.append(style)
                self.offset += offset
                continue

            let, offset = PairDocASTLet(self.token_list).match(self.offset)
            if let:
                ret.append(let)
                self.offset += offset
                continue
            assign, offset = PairDocASTAssign(self.token_list).match(self.offset)
            if assign:
                ret.append(assign)
                self.offset += offset
                continue
            order_change, offset = PairDocASTOrderChange(self.token_list).match(self.offset)
            if order_change:
                ret.append(order_change)
                self.offset += offset
                continue
            function_call, offset = PairDocASTFunctionCall(self.token_list).match(self.offset)
            if function_call:
                ret.append(function_call)
                self.offset += offset
                continue
            special, offset = PairDocSpecial(self.token_list).match(self.offset)
            if special:
                ret.append(special)
                self.offset += offset
                continue
            unfunctional, offset = PairDocUnFunctional(self.token_list).match(self.offset)
            if unfunctional:
                ret.append(unfunctional)
                self.offset += offset
                continue
            never_return, offset = PairDocASTNeverReturn(self.token_list).match(self.offset)
            if never_return:
                ret.append(never_return)
                self.offset += offset
                continue
            sub_doc, offset = PairDocASTSubDocument(self.token_list).match(self.offset)
            if sub_doc:
                ret.append(sub_doc)
                self.offset += offset
                continue
            function_def, offset = PairDocASTFunctionDef(self.token_list).match(self.offset)
            if function_def:
                ret.append(function_def)
                self.offset += offset
                continue

            else:
                ret.append(PairDocASTNode(PairDocASTNodeTypes.TEXT, _concat(self.token_list[self.offset])))
                self.offset += 1
        return ret
