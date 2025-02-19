import re
import base64

DEBUG = False

class PairDocTokenType:
    TokenType_COMMENT = 'COMMENT'
    TokenType_NUMBER = 'NUMBER'
    TokenType_STRING = 'STRING'
    TokenType_SYMBOL = 'SYMBOL'
    TokenType_IDENTIFIER = 'IDENTIFIER'
    TokenType_BASE64 = 'BASE64'


class PairDocLexer:
    def tokenize(self, str):
        tokens = []
        currpos = 0

        def skip_space():
            nonlocal currpos
            while currpos < len(str) and str[currpos] in (' ', '\t', '\n', '\r'):
                currpos += 1

        def next_line():
            nonlocal currpos
            while currpos < len(str) and str[currpos] not in ('\n', '\r'):
                currpos += 1

        def test_string(test_str):
            nonlocal currpos
            if currpos + len(test_str) > len(str):
                return False
            return str[currpos:currpos + len(test_str)] == test_str

        def test_number(pos):
            number_pattern = re.compile(r'^\d*\.?\d+([eE][-+]?\d+)?')
            match_ = number_pattern.match(str[pos:])
            return match_.end() if match_ else 0

        def read_number():
            nonlocal currpos
            length = test_number(currpos)
            if length:
                current_token = str[currpos:currpos + length]
                currpos += length
                return current_token
            return None

        def read_base64():
            nonlocal currpos
            current_token = ''
            if test_string('$"'):
                currpos += 2
                while currpos < len(str):
                    if str[currpos] == '\\':
                        currpos += 1
                        if currpos < len(str):
                            escape_char = str[currpos]
                            if escape_char == 'n':
                                current_token += '\n'
                            elif escape_char == 't':
                                current_token += '\t'
                            elif escape_char in ('"', '\\'):
                                current_token += escape_char
                            elif escape_char == 'u':
                                try:
                                    currpos += 1
                                    if currpos < len(str):
                                        hex_str = str[currpos:currpos + 4]
                                        current_token += chr(int(hex_str, 16))
                                        currpos += 3
                                    else:
                                        return None  # Error: unexpected end of string
                                except ValueError:
                                    return None
                            else:
                                current_token += '\\' + escape_char
                            currpos += 1
                        else:
                            return None  # Error: unexpected end of string
                    elif str[currpos] == '"':
                        currpos += 1
                        return current_token
                    else:
                        current_token += str[currpos]
                        currpos += 1
        def read_string():
            nonlocal currpos
            current_token = ''
            if test_string('R"'):
                currpos += 2
                divider = ''
                while currpos < len(str) and str[currpos] != '(':
                    divider += str[currpos]
                    currpos += 1
                if currpos < len(str):
                    currpos += 1  # skip '('
                    end_divider = ')' + divider + '"'
                    while currpos < len(str) and not test_string(end_divider):
                        if str[currpos] == '\\':  # Handle escape sequences
                            currpos += 1
                            if currpos < len(str):
                                escape_char = str[currpos]
                                if escape_char == 'n':
                                    current_token += '\n'
                                elif escape_char == 't':
                                    current_token += '\t'
                                elif escape_char in ('"', '\\'):
                                    current_token += escape_char
                                elif escape_char == 'u':
                                    try:
                                        currpos += 1
                                        if currpos < len(str):
                                            hex_str = str[currpos:currpos + 4]
                                            current_token += chr(int(hex_str, 16))
                                            currpos += 3
                                        else:
                                            return None  # Error: unexpected end of string
                                    except ValueError:
                                        return None
                                else:
                                    current_token += '\\' + escape_char  # Keep unrecognized escape sequences
                                currpos += 1
                            else:
                                return None  # Error: unexpected end of string
                        else:
                            current_token += str[currpos]
                            currpos += 1
                    if currpos < len(str):
                        currpos += len(end_divider)  # Skip the closing delimiter
                        return current_token
            if test_string('"""'):
                currpos += 3
                while currpos < len(str):
                    if test_string('"""'):
                        currpos += 3
                        return current_token
                    if str[currpos] == '\\':
                        currpos += 1
                        if currpos < len(str):
                            escape_char = str[currpos]
                            if escape_char == 'n':
                                current_token += '\n'
                            elif escape_char == 't':
                                current_token += '\t'
                            elif escape_char in ('"', '\\'):
                                current_token += escape_char
                            elif escape_char == 'u':
                                try:
                                    currpos += 1
                                    if currpos < len(str):
                                        hex_str = str[currpos:currpos + 4]
                                        current_token += chr(int(hex_str, 16))
                                        currpos += 3
                                    else:
                                        return None
                                except ValueError:
                                    return None
                            else:
                                current_token += '\\' + escape_char
                            currpos += 1
                        else:
                            return None
                    else:
                        current_token += str[currpos]
                        currpos += 1

            if test_string("'''"):
                currpos += 3
                while currpos < len(str):
                    if test_string("'''"):
                        currpos += 3
                        return current_token
                    if str[currpos] == '\\':
                        currpos += 1
                        if currpos < len(str):
                            escape_char = str[currpos]
                            if escape_char == 'n':
                                current_token += '\n'
                            elif escape_char == 't':
                                current_token += '\t'
                            elif escape_char in ('"', '\\'):
                                current_token += escape_char
                            elif escape_char == 'u':
                                try:
                                    currpos += 1
                                    if currpos < len(str):
                                        hex_str = str[currpos:currpos + 4]
                                        current_token += chr(int(hex_str, 16))
                                        currpos += 3
                                    else:
                                        return None
                                except ValueError:
                                    return None
                            else:
                                current_token += '\\' + escape_char
                            currpos += 1
                        else:
                            return None
                    else:
                        current_token += str[currpos]
                        currpos += 1
            match_pair = {
                '"': '"',
                "'": "'",
                '“': '”',
                # Add more pairs as needed
            }
            start_char = str[currpos]
            if start_char in match_pair:
                currpos += 1
                while currpos < len(str):
                    if str[currpos] == '\\':
                        currpos += 1
                        if currpos < len(str):
                            escape_char = str[currpos]
                            if escape_char == 'n':
                                current_token += '\n'
                            elif escape_char == 't':
                                current_token += '\t'
                            elif escape_char in (start_char, '\\'):
                                current_token += escape_char
                            elif escape_char == 'u':
                                try:
                                    currpos += 1
                                    if currpos < len(str):
                                        hex_str = str[currpos:currpos + 4]
                                        current_token += chr(int(hex_str, 16))
                                        currpos += 3
                                    else:
                                        return None  # Error: unexpected end of string
                                except ValueError:
                                    return None
                            else:
                                current_token += '\\' + escape_char
                            currpos += 1
                        else:
                            return None  # Error: unexpected end of string
                    elif str[currpos] == match_pair[start_char]:
                        currpos += 1
                        return current_token
                    else:
                        current_token += str[currpos]
                        currpos += 1

            return None


        def read_token():
            nonlocal currpos
            current_token = ''
            while currpos < len(str):
                if str[currpos] in (' ', '\t', '\n', '\r', '\'', '"'):
                    break
                if currpos < len(str) - 2:
                    three_char = str[currpos:currpos + 3]
                    if self.is_operator(three_char, 0):
                        break
                if currpos < len(str) - 1:
                    two_char = str[currpos:currpos + 2]
                    if self.is_operator(two_char, 0):
                        break
                one_char = str[currpos]
                if self.is_operator(one_char, 0):
                    break
                current_token += one_char
                currpos += 1
            return current_token

        def read_operator():
            nonlocal currpos
            if currpos < len(str) - 2:
                three_char = str[currpos:currpos + 3]
                if self.is_operator(three_char, 0):
                    currpos += 3
                    return three_char
            if currpos < len(str) - 1:
                two_char = str[currpos:currpos + 2]
                if self.is_operator(two_char, 0):
                    currpos += 2
                    return two_char
            if currpos < len(str):
                one_char = str[currpos]
                if self.is_operator(one_char, 0):
                    currpos += 1
                    return one_char
            return None

        def read_comment():
            nonlocal currpos
            current_token = ''
            if test_string('//'):
                currpos += 2
                while currpos < len(str) and str[currpos] not in ('\n', '\r'):
                    current_token += str[currpos]
                    currpos += 1
                return current_token
            if test_string('/*'):
                currpos += 2
                while currpos < len(str) and not test_string('*/'):
                    current_token += str[currpos]
                    currpos += 1
                if currpos < len(str):
                    currpos += 2  # Skip closing */
                return current_token
            return None

        while True:
            skip_space()
            if currpos >= len(str):
                break
            
            token = None
            position = currpos

            if (comment := read_comment()) is not None:
                tokens.append({'token': comment, 'type': PairDocTokenType.TokenType_COMMENT, 'position': position})
            elif (number := read_number()) is not None:
                tokens.append({'token': number, 'type': PairDocTokenType.TokenType_NUMBER, 'position': position})
            elif (string := read_string()) is not None:
                tokens.append({'token': string, 'type': PairDocTokenType.TokenType_STRING, 'position': position})
            elif (string := read_base64()) is not None:
                tokens.append({'token': string, 'type': PairDocTokenType.TokenType_BASE64, 'position': position})
            elif (operator := read_operator()) is not None:
                tokens.append({'token': operator, 'type': PairDocTokenType.TokenType_SYMBOL, 'position': position})
            else:
                token = read_token()
                if token:
                    tokens.append({'token': token, 'type': PairDocTokenType.TokenType_IDENTIFIER, 'position': position})

        return tokens

    def is_operator(self, t, type):
        l = (t in {"+", "-", "*", "/", "\\", "%", "&", "!", "^", "~", "=", "==", ">", "<", "<=", ">=", "!=", "?=", "|", "?", ":>", "#",
                    "&&", ",", ".", "\n", ":", "->", "<<", ">>", "/*", "*/", ";", " ", ":=", "|>", "<|", "::", "--", "=>", "++", "||", ">>", "<<", '"""', "'''"})
        if type == 0:
            l = l or (t in {"(", ")", "[", "]", "{", "}"})
        return l

    def reject_comments(self, tokens):
        return [token for token in tokens if token['type'] != PairDocTokenType.TokenType_COMMENT]
    
    def concat_multi_line_string(self, tokens):
        new_tokens = []
        multi_line_string = None
        start_positon = None
        for token in tokens:
            if token['type'] == PairDocTokenType.TokenType_STRING:
                if multi_line_string is None:
                    multi_line_string = token['token']
                    start_positon = token['position']
                else:
                    multi_line_string += token['token']
            else:
                if multi_line_string is not None:
                    new_tokens.append({'token': multi_line_string, 'type': PairDocTokenType.TokenType_STRING, 'position': start_positon})
                    multi_line_string = None
                    start_positon = None
                new_tokens.append(token)
        if multi_line_string is not None:
            new_tokens.append({'token': multi_line_string, 'type': PairDocTokenType.TokenType_STRING, 'position': start_positon})
        return new_tokens
    
    # 合并负数
    def concat_negative_number(self, tokens):
        new_tokens = []
        offset = 0
        while offset < len(tokens):
            if tokens[offset]['token'] == '-' and tokens[offset]['type'] == PairDocTokenType.TokenType_SYMBOL:
                if offset + 1 < len(tokens) and tokens[offset + 1]['type'] == PairDocTokenType.TokenType_NUMBER and (offset == 0 or tokens[offset - 1]['type'] == PairDocTokenType.TokenType_SYMBOL):
                    new_tokens.append({'token': '-' + tokens[offset + 1]['token'], 'type': PairDocTokenType.TokenType_NUMBER, 'position': tokens[offset]['position']})
                    offset += 2
                    continue
            new_tokens.append(tokens[offset])
            offset += 1
        return new_tokens

class PairDocTokenizer:
    def __init__(self):
        self.lexer = PairDocLexer()

    def parse(self, text):
        tokens = self.lexer.tokenize(text)
        tokens = self.lexer.reject_comments(tokens)
        return tokens