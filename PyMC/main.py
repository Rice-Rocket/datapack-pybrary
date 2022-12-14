from string_with_arrows import *
import re
import string
import os


#######################
# REGULAR EXPRESSIONS #
#######################

re_digit = '0123456789'
re_int = re.compile('[0-9]+')
re_float = re.compile('[0-9]+\.[0-9]*')
re_letters = string.ascii_letters
re_letters_digits = re_letters + re_digit

##########
# ERRORS #
##########

class Error:
    def __init__(self, pos_start, pos_end, error_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details
        
    def as_string(self):
        result = f'{self.error_name}: {self.details}'
        result += f'\nFile {self.pos_start.file}, line {self.pos_start.line + 1}'
        result += '\n\n' + string_with_arrows(self.pos_start.filetxt, self.pos_start, self.pos_end)
        return result
    
class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Illegal Character', details)
    
class ExpectedCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Expected Character', details)
        
class InvalidSyntaxError(Error):
    def __init__(self, pos_start, pos_end, details=''):
        super().__init__(pos_start, pos_end, 'Invalid Syntax', details)
        
class RTError(Error):
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, 'Runtime Error', details)
        self.context = context
        
    def as_string(self):
        result = self.generate_traceback()
        result = f'{self.error_name}: {self.details}'
        result += '\n\n' + string_with_arrows(self.pos_start.filetxt, self.pos_start, self.pos_end)
        return result
        
    def generate_traceback(self):
        result = ''
        pos = self.pos_start
        context = self.context
        
        while context:
            result = f'  File {pos.file}, line {str(pos.line + 1)}, in {context.display_name}\n' + result
            pos = context.parent_entry_pos
            context = context.parent
            
        return 'Traceback (most recent call last):\n' + result
        
############
# POSITION #
############
        
class Position:
    def __init__(self, index, line, col, file, filetxt):
        self.index = index
        self.line = line
        self.col = col
        self.file = file
        self.filetxt = filetxt
        
    def advance(self, char=None):
        self.index += 1
        self.col += 1
        
        if char == '\n':
            self.line += 1
            self.col = 0
            
        return self
    
    def copy(self):
        return Position(self.index, self.line, self.col, self.file, self.filetxt)
    
    

##########
# TOKENS #
##########

tt_int = 'int'
tt_float = 'float'
tt_string = 'string'
tt_identifier = 'identifier'
tt_keyword = 'keyword'
tt_plus = 'plus'
tt_minus = 'minus'
tt_mul = 'mul'
tt_div = 'div'
tt_power = 'power'
tt_eq = 'eq'
tt_lparen = 'lparen'
tt_rparen = 'rparen'
tt_lsquare = 'lsquare'
tt_rsquare = 'rsquare'
tt_ee = 'ee'
tt_ne = 'ne'
tt_lt = 'lt'
tt_gt = 'gt'
tt_lte = 'lte'
tt_gte = 'gte'
tt_comma = 'comma'
tt_arrow = 'arrow'
tt_newline = 'newline'
tt_eof = 'eof'

KEYWORDS = [
    'var',
    'and',
    'or',
    'not',
    'if',
    'then',
    'elif',
    'else',
    'for',
    'to',
    'step',
    'in',
    'while',
    'def',
    'end',
    'return',
    'continue',
    'break'
]




class Token:
    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        self.type = type_
        self.value = value
        
        if pos_start:
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy()
            self.pos_end.advance()
        
        if pos_end:
            self.pos_end = pos_end.copy()
            
    def matches(self, type_, value):
        return self.type == type_ and self.value == value
        
    def __repr__(self):
        if self.value: return f'{self.type}:{self.value}'
        return f'{self.type}'
    
    
#########
# LEXER #
#########
    
class Lexer:
    def __init__(self, file, text):
        self.file = file
        self.text = text
        self.pos = Position(-1, 0, -1, file, text)
        self.current_char = None
        self.advance()
        
    def advance(self):
        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.index] if self.pos.index < len(self.text) else None
        
    def make_tokens(self):
        tokens = []
        
        while self.current_char != None:
            
            if self.current_char in ' \t':
                self.advance()
                
            elif self.current_char == '#':
                self.skip_comment()
                
            elif self.current_char in ';\n':
                tokens.append(Token(tt_newline, pos_start=self.pos))
                self.advance()
                
            elif self.current_char in re_digit:
                tokens.append(self.make_number())
                
            elif self.current_char in re_letters:
                tokens.append(self.make_identifier())
                
            elif self.current_char == '"':
                tokens.append(self.make_string())
                
            elif self.current_char == '+':
                tokens.append(Token(tt_plus, pos_start=self.pos))
                self.advance()
                
            elif self.current_char == '-':
                tokens.append(self.make_minus_or_arrow())
                
            elif self.current_char == '*':
                tokens.append(Token(tt_mul, pos_start=self.pos))
                self.advance()
                
            elif self.current_char == '/':
                tokens.append(Token(tt_div, pos_start=self.pos))
                self.advance()
                
            elif self.current_char == '^':
                tokens.append(Token(tt_power, pos_start=self.pos))
                self.advance()
                
            elif self.current_char == '(':
                tokens.append(Token(tt_lparen, pos_start=self.pos))
                self.advance()
                
            elif self.current_char == ')':
                tokens.append(Token(tt_rparen, pos_start=self.pos))
                self.advance()
                
            elif self.current_char == '[':
                tokens.append(Token(tt_lsquare, pos_start=self.pos))
                self.advance()
                
            elif self.current_char == ']':
                tokens.append(Token(tt_rsquare, pos_start=self.pos))
                self.advance()
                
            elif self.current_char == '!':
                token, error = self.make_not_equals()
                if error: return [], error
                tokens.append(token)
                
            elif self.current_char == '=':
                tokens.append(self.make_equals())
                
            elif self.current_char == '<':
                tokens.append(self.less_than())
                
            elif self.current_char == '>':
                tokens.append(self.greater_than())
                
            elif self.current_char == ',':
                tokens.append(Token(tt_comma, pos_start=self.pos))
                self.advance()
            
            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, "'" + char + "'")
        
        tokens.append(Token(tt_eof, pos_start=self.pos))
        return tokens, None
        
    def make_number(self):
        num_str = ''
        dot_count = 0
        pos_start = self.pos.copy()
        
        while self.current_char != None and self.current_char in re_digit + '.':
            if self.current_char == '.':
                if dot_count == 1: break
                dot_count += 1
                num_str += '.'
            else:
                num_str += self.current_char
            self.advance()
                
        if dot_count == 0:
            return Token(tt_int, int(num_str), pos_start, self.pos)
        else:
            return Token(tt_float, float(num_str), pos_start, self.pos)
        
    def make_string(self):
        string = ''
        pos_start = self.pos.copy()
        escape_char = False
        self.advance()
        
        escape_chars = {
            'n': '\n',
            't': '\t'
        }
        
        while self.current_char != None and (self.current_char != '"' or escape_char):
            if escape_char:
                string += escape_chars.get(self.current_char, self.current_char)
            else:
                if self.current_char == '\\':
                   escape_char = True
                else:
                    string += self.current_char
            self.advance()
            escape_char = False
            
        self.advance()
        return Token(tt_string, string, pos_start, self.pos)
        
    def make_identifier(self):
        id_str = ''
        pos_start = self.pos.copy()
        
        while self.current_char != None and self.current_char in re_letters_digits + '_':
            id_str +=self.current_char
            self.advance()
            
        token_type = tt_keyword if id_str in KEYWORDS else tt_identifier
        return Token(token_type, id_str, pos_start, self.pos)
    
    def make_minus_or_arrow(self):
        token_type = tt_minus
        pos_start = self.pos.copy()
        self.advance()
        
        if self.current_char == '>':
            self.advance()
            token_type = tt_arrow
            
        return Token(token_type, pos_start=pos_start, pos_end=self.pos)
    
    def make_not_equals(self):
        pos_start = self.pos.copy()
        self.advance()
        
        if self.current_char == '=':
            self.advance()
            return Token(tt_ne, pos_start=pos_start, pos_end=self.pos), None
        
        self.advance()
        return None, ExpectedCharError(pos_start, self.pos, "'=' (after '!')")
    
    def make_equals(self):
        token_type = tt_eq
        pos_start = self.pos.copy()
        self.advance()
        
        if self.current_char == '=':
            self.advance()
            token_type = tt_ee
            
        return Token(token_type, pos_start=pos_start, pos_end=self.pos)
    
    def less_than(self):
        token_type = tt_lt
        pos_start = self.pos.copy()
        self.advance()
        
        if self.current_char == '=':
            self.advance()
            token_type = tt_lte
            
        return Token(token_type, pos_start=pos_start, pos_end=self.pos)
    
    def greater_than(self):
        token_type = tt_gt
        pos_start = self.pos.copy()
        self.advance()
        
        if self.current_char == '=':
            self.advance()
            token_type = tt_gte
            
        return Token(token_type, pos_start=pos_start, pos_end=self.pos)
    
    def skip_comment(self):
        self.advance()
        
        while self.current_char != '\n':
            self.advance()
        
        self.advance()
        
#########
# NODES #
#########

class NumberNode:
    def __init__(self, token):
        self.token = token
        
        self.pos_start = self.token.pos_start
        self.pos_end = self.token.pos_end
        
    def __repr__(self):
        return f'{self.token}'
    
class StringNode:
    def __init__(self, token):
        self.token = token
        
        self.pos_start = self.token.pos_start
        self.pos_end = self.token.pos_end
        
    def __repr__(self):
        return f'{self.token}'
    
class ListNode:
    def __init__(self, element_nodes, pos_start, pos_end):
        self.element_nodes = element_nodes
        
        self.pos_start = pos_start
        self.pos_end = pos_end
    
class VarAccessNode:
    def __init__(self, var_name_token):
        self.var_name_token = var_name_token
        
        self.pos_start = self.var_name_token.pos_start
        self.pos_end = self.var_name_token.pos_end
        
class VarAssignNode:
    def __init__(self, var_name_token, value):
        self.var_name_token = var_name_token
        self.value_node = value
        
        self.pos_start = self.var_name_token.pos_start
        self.pos_end = self.value_node.pos_end

class BinaryOpNode:
    def __init__(self, left_node, op_token, right_node):
        self.left_node = left_node
        self.right_node = right_node
        self.op_token = op_token
        
        self.pos_start = self.left_node.pos_start
        self.pos_end = self.right_node.pos_end
        
    def __repr__(self):
        return f'({self.left_node}, {self.op_token}, {self.right_node})'
    
    
class UnaryOpNode:
    def __init__(self, op_token, node):
        self.op_token = op_token
        self.node = node
        
        self.pos_start = self.op_token.pos_start
        self.pos_end = node.pos_end
        
    def __repr__(self):
        return f'({self.op_token}, {self.node})'
    
class IfNode:
    def __init__(self, cases, else_case):
        self.cases = cases
        self.else_case = else_case
        
        self.pos_start = self.cases[0][0].pos_start
        self.pos_end = (self.else_case or self.cases[len(self.cases) - 1])[0].pos_end
        
class ForNode:
    def __init__(self, var_name, start_value, end_value, step_value, body, should_return_null):
        self.var_name_token = var_name
        self.start_value_node = start_value
        self.end_value_node = end_value
        self.step_value_node = step_value
        self.body_node = body
        self.should_return_null = should_return_null
        
        self.pos_start = self.var_name_token.pos_start
        self.pos_end = self.body_node.pos_end
        
class WhileNode:
    def __init__(self, condition, body, should_return_null):
        self.condition_node = condition
        self.body_node = body
        self.should_return_null = should_return_null
        
        self.pos_start = self.condition_node.pos_start
        self.pos_end = self.body_node.pos_end
        
class FuncDefNode:
    def __init__(self, var_name_token, arg_name_tokens, body_node, should_auto_return):
        self.var_name_token = var_name_token
        self.arg_name_tokens = arg_name_tokens
        self.body_node = body_node
        self.should_auto_return = should_auto_return
        
        if self.var_name_token:
            self.pos_start = self.var_name_token.pos_start
        elif len(self.arg_name_tokens) > 0:
            self.pos_start = self.arg_name_tokens[0].pos_start
        else:
            self.pos_start = self.body_node.pos_start
            
        self.pos_end = self.body_node.pos_end
        
class CallNode:
    def __init__(self, node_to_call, arg_nodes):
        self.node_to_call = node_to_call
        self.arg_nodes = arg_nodes
        
        self.pos_start = self.node_to_call.pos_start
        
        if len(self.arg_nodes) > 0:
            self.pos_end = self.arg_nodes[len(self.arg_nodes) - 1].pos_end
        else:
            self.pos_end = self.node_to_call.pos_end
            
class ReturnNode:
    def __init__(self, node_to_return, pos_start, pos_end):
        self.node_to_return = node_to_return
        
        self.pos_start = pos_start
        self.pos_end = pos_end
        
class ContinueNode:
    def __init__(self, pos_start, pos_end):
        self.pos_start = pos_start
        self.pos_end = pos_end
        
class BreakNode:
    def __init__(self, pos_start, pos_end):
        self.pos_start = pos_start
        self.pos_end = pos_end
    
    
################
# PARSE RESULT #
################

class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None
        self.last_registered_advance_count = 0
        self.advance_count = 0
        self.to_reverse_count = 0
        
    def register_advancement(self):
        self.last_registered_advance_count = 1
        self.advance_count += 1
        
    def register(self, res):
        self.last_registered_advance_count = res.advance_count
        self.advance_count += res.advance_count
        if res.error: self.error = res.error
        return res.node
    
    def try_register(self, res):
        if res.error:
            self.to_reverse_count = res.advance_count
            return None
        return self.register(res)
    
    def success(self, node):
        self.node = node
        return self
    
    def fail(self, error):
        if not self.error or self.last_registered_advance_count == 0:
            self.error = error
        return self
    
    
##########
# PARSER #
##########

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.token_index = -1
        self.advance()
        
    def advance(self):
        self.token_index += 1
        self.update_current_token()
        return self.current_token
    
    def reverse(self, amount=1):
        self.token_index -= amount
        self.update_current_token()
        return self.current_token
    
    def update_current_token(self):
        if self.token_index >= 0 and self.token_index < len(self.tokens):
            self.current_token = self.tokens[self.token_index]

    def parse(self):
        res = self.statements()
        if not res.error and self.current_token.type != tt_eof:
            return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected '+', '-', '*' or '/'"))
        return res
    
################################

    def statements(self):
        res = ParseResult()
        statements = []
        pos_start = self.current_token.pos_start.copy()
        
        while self.current_token.type == tt_newline:
            res.register_advancement()
            self.advance()
            
        statement = res.register(self.statement())
        if res.error: return res
        statements.append(statement)
        
        more_statements = True
        
        while True:
            newline_count = 0
            while self.current_token.type == tt_newline:
                res.register_advancement()
                self.advance()
                newline_count += 1
            if newline_count == 0:
                more_statements = False
                
            if not more_statements: break
            statement = res.try_register(self.statement())
            if not statement:
                self.reverse(res.to_reverse_count)
                more_statements = False
                continue
            statements.append(statement)
        
        return res.success(ListNode(statements, pos_start, self.current_token.pos_end.copy()))
    
    def statement(self):
        res = ParseResult()
        pos_start = self.current_token.pos_start.copy()
        
        if self.current_token.matches(tt_keyword, 'return'):
            res.register_advancement()
            self.advance()
            
            expr = res.try_register(self.expr())
            if not expr:
                self.reverse(res.to_reverse_count)
            return res.success(ReturnNode(expr, pos_start, self.current_token.pos_start.copy()))
        
        if self.current_token.matches(tt_keyword, 'continue'):
            res.register_advancement()
            self.advance()
            return res.success(ContinueNode(pos_start, self.current_token.pos_start.copy()))
        
        if self.current_token.matches(tt_keyword, 'break'):
            res.register_advancement()
            self.advance()
            return res.success(BreakNode(pos_start, self.current_token.pos_start.copy()))
        
        expr = res.register(self.expr())
        if res.error:
            return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected 'return', 'continue', 'break', 'var', 'for', 'while', 'if', 'def', int, float, identifier, '+', '-', '(', '[' or 'not'"))

        return res.success(expr)

    def list_expr(self):
        res = ParseResult()
        elem_nodes = []
        pos_start = self.current_token.pos_start.copy()
        
        if self.current_token.type != tt_lsquare:
            return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, f"Expected '['"))
        
        res.register_advancement()
        self.advance()
        
        if self.current_token.type == tt_rsquare:
            res.register_advancement()
            self.advance()
        else:
            elem_nodes.append(res.register(self.expr()))
            if res.error:
                return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected ']', 'var', 'if', 'for', 'while', 'fun', int, float, identifier, '+', '-', '[' or 'not'"))
            
            while self.current_token.type == tt_comma:
                res.register_advancement()
                self.advance()
                
                elem_nodes.append(res.register(self.expr()))
                if res.error: return res
                
            if self.current_token.type != tt_rsquare:
                return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, f"Expected ',' or ']'"))
            
            res.register_advancement()
            self.advance()
            
        return res.success(ListNode(elem_nodes, pos_start, self.current_token.pos_end.copy()))

    def if_expr(self):
        res = ParseResult()
        all_cases = res.register(self.if_expr_cases('if'))
        if res.error: return res
        cases, else_case = all_cases
        return res.success(IfNode(cases, else_case))
    
    def if_expr_b(self):
        return self.if_expr_cases('elif')
    
    def if_expr_c(self):
        res = ParseResult()
        else_case = None
        
        if self.current_token.matches(tt_keyword, 'else'):
            res.register_advancement()
            self.advance()
            
            if self.current_token.type == tt_newline:
                res.register_advancement()
                self.advance()
                
                statements = res.register(self.statements())
                if res.error: return res
                else_case = (statements, True)
                
                if self.current_token.matches(tt_keyword, 'end'):
                    res.register_advancement()
                    self.advance()
                else:
                    return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected 'end'"))
            else:
                expr = res.register(self.statement())
                if res.error: return res
                else_case = (expr, False)
                
        return res.success(else_case)
    
    def if_expr_b_or_c(self):
        res = ParseResult()
        cases, else_case = [], None
        
        if self.current_token.matches(tt_keyword, 'elif'):
            all_cases = res.register(self.if_expr_b())
            if res.error: return res
            cases, else_case = all_cases
        else:
            else_case = res.register(self.if_expr_c())
            if res.error: return res
            
        return res.success((cases, else_case))
    
    def if_expr_cases(self, case_keyword):
        res = ParseResult()
        cases = []
        else_case = None
        
        if not self.current_token.matches(tt_keyword, case_keyword):
            return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, f"Expected '{case_keyword}'"))
                            
        res.register_advancement()
        self.advance()
        
        condition = res.register(self.expr())
        if res.error: return res
        
        if not self.current_token.matches(tt_keyword, 'then'):
            return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected 'then'"))
        
        res.register_advancement()
        self.advance()
        
        if self.current_token.type == tt_newline:
            res.register_advancement()
            self.advance()
            
            statements = res.register(self.statements())
            if res.error: return res
            cases.append((condition, statements, True))
            
            if self.current_token.matches(tt_keyword, 'end'):
                res.register_advancement()
                self.advance()
            else:
                all_cases = res.register(self.if_expr_b_or_c())
                if res.error: return res
                new_cases, else_case = all_cases
                cases.extend(new_cases)
        else:
            expr = res.register(self.statement())
            if res.error: return res
            cases.append((condition, expr, False))
            
            all_cases = res.register(self.if_expr_b_or_c())
            if res.error: return res
            new_cases, else_case = all_cases
            cases.extend(new_cases)
        
        return res.success((cases, else_case))
    
    def for_expr(self):
        res = ParseResult()
        
        if not self.current_token.matches(tt_keyword, 'for'):
            return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, f"Expected 'for"))
        
        res.register_advancement()
        self.advance()
        
        if self.current_token.type != tt_identifier:
            return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, f"Expected identifier"))
        
        var_name = self.current_token
        res.register_advancement()
        self.advance()
        
        if not self.current_token.matches(tt_keyword, 'in'):
            return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, f"Expected 'is'"))
        
        res.register_advancement()
        self.advance()
        
        start_value = res.register(self.expr())
        if res.error: return res
        
        if not self.current_token.matches(tt_keyword, 'to'):
            return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, f"Expected 'to'"))
        
        res.register_advancement()
        self.advance()
        
        end_value = res.register(self.statement())
        if res.error: return res
        
        if self.current_token.matches(tt_keyword, 'step'):
            res.register_advancement()
            self.advance()
            
            step_value = res.register(self.expr())
            if res.error: return res
            
        else:
            step_value = None
            
        if not self.current_token.matches(tt_keyword, 'then'):
            return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, f"Expected 'then'"))
        
        res.register_advancement()
        self.advance()
        
        if self.current_token.type == tt_newline:
            res.register_advancement()
            self.advance()
            
            body = res.register(self.statements())
            if res.error: return res
            
            if not self.current_token.matches(tt_keyword, 'end'):
                return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected 'end'"))
            
            res.register_advancement()
            self.advance()
            
            return res.success(ForNode(var_name, start_value, end_value, step_value, body, True))
        
        body = res.register(self.expr())
        if res.error: return res
        
        return res.success(ForNode(var_name, start_value, end_value, step_value, body, False))
    
    def while_expr(self):
        res = ParseResult()
        
        if not self.current_token.matches(tt_keyword, 'while'):
            return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, f"Expected 'while'"))
        
        res.register_advancement()
        self.advance()
        
        condition = res.register(self.expr())
        if res.error: return res
        
        if not self.current_token.matches(tt_keyword, 'then'):
            return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, f"Expected 'then'"))
        
        res.register_advancement()
        self.advance()
        
        if self.current_token.type == tt_newline:
            res.register_advancement()
            self.advance()
            
            body = res.register(self.statements())
            if res.error: return res
            
            if not self.current_token.matches(tt_keyword, 'end'):
                return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected 'end'"))
            
            res.register_advancement()
            self.advance()
            
            return res.success(WhileNode(condition, body, True))
        
        body = res.register(self.statement())
        if res.error: return res
        
        return res.success(WhileNode(condition, body, False))
    
    def func_def(self):
        res = ParseResult()
        
        if not self.current_token.matches(tt_keyword, 'def'):
            return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, f"Expected 'def'"))
        
        res.register_advancement()
        self.advance()
        
        if self.current_token.type == tt_identifier:
            var_name_token = self.current_token
            res.register_advancement()
            self.advance()
            if self.current_token.type != tt_lparen:
                return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, f"Expected '('"))
            
        else:
            var_name_token = None
            if self.current_token.type != tt_lparen:
                return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, f"Expected identifier or '('"))
            
        res.register_advancement()
        self.advance()
        
        arg_name_tokens = []
        if self.current_token.type == tt_identifier:
            arg_name_tokens.append(self.current_token)
            res.register_advancement()
            self.advance()
            
            while self.current_token.type == tt_comma:
                res.register_advancement()
                self.advance()
                
                if self.current_token.type != tt_identifier:
                    return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, f"Expected identifier"))
                
                arg_name_tokens.append(self.current_token)
                res.register_advancement()
                self.advance()
                
            if self.current_token.type != tt_rparen:
                return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, f"Expected ',' or ')'"))
            
        else:
            if self.current_token.type != tt_rparen:
                return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, f"Expected identifier or ')'"))
            
        res.register_advancement()
        self.advance()
        
        if self.current_token.type == tt_arrow:
        
            res.register_advancement()
            self.advance()
            
            body = res.register(self.expr())
            if res.error: return res
            
            return res.success(FuncDefNode(var_name_token, arg_name_tokens, body, True))
        
        if self.current_token.type != tt_newline:
            return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected '->' or New Line"))
        
        res.register_advancement()
        self.advance()
        
        body = res.register(self.statements())
        if res.error: return res
        
        if not self.current_token.matches(tt_keyword, 'end'):
            return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected 'end'"))
        
        res.register_advancement()
        self.advance()
        
        return res.success(FuncDefNode(var_name_token, arg_name_tokens, body, False))
    
    def call(self):
        res = ParseResult()
        atom = res.register(self.atom())
        if res.error: return res
        
        if self.current_token.type == tt_lparen:
            res.register_advancement()
            self.advance()
            
            arg_nodes = []
            
            if self.current_token.type == tt_rparen:
                res.register_advancement()
                self.advance()
            else:
                arg_nodes.append(res.register(self.expr()))
                if res.error:
                    return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected ')', 'var', 'if', 'for', 'while', 'def', int, float, identifier, '+', '-', '(', '[' or 'not'"))
                
                while self.current_token.type == tt_comma:
                    res.register_advancement()
                    self.advance()
                    
                    arg_nodes.append(res.register(self.expr()))
                    if res.error: return res
                    
                if self.current_token.type != tt_rparen:
                    return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, f"Expected ',' or ')'"))
                
                res.register_advancement()
                self.advance()
                
            return res.success(CallNode(atom, arg_nodes))
        return res.success(atom)

    def atom(self):
        res = ParseResult()
        token = self.current_token
        
        if token.type in (tt_int, tt_float):
            res.register_advancement()
            self.advance()
            return res.success(NumberNode(token))
        
        if token.type == tt_string:
            res.register_advancement()
            self.advance()
            return res.success(StringNode(token))
        
        elif token.type == tt_identifier:
            res.register_advancement()
            self.advance()
            return res.success(VarAccessNode(token))
        
        elif token.type == tt_lparen: 
            res.register_advancement()
            self.advance()
            expr = res.register(self.expr())
            if res.error: return res
            if self.current_token.type == tt_rparen:
                res.register_advancement()
                self.advance()
                return res.success(expr)
            else: 
                return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected ')'"))
        
        elif token.type == tt_lsquare:
            list_expr = res.register(self.list_expr())
            if res.error: return res
            return res.success(list_expr)
            
        elif token.matches(tt_keyword, 'if'):
            if_expr = res.register(self.if_expr())
            if res.error: return res
            return res.success(if_expr)
        
        elif token.matches(tt_keyword, 'for'):
            for_expr = res.register(self.for_expr())
            if res.error: return res
            return res.success(for_expr)
        
        elif token.matches(tt_keyword, 'while'):
            while_expr = res.register(self.while_expr())
            if res.error: return res
            return res.success(while_expr)
        
        elif token.matches(tt_keyword, 'def'):
            func_def = res.register(self.func_def())
            if res.error: return res
            return res.success(func_def)
            
        
        return res.fail(InvalidSyntaxError(token.pos_start, token.pos_end, "Expected int, float, identifier, '+', '-', '(', '[', 'if', 'for', 'while', 'def'"))
    
    def power(self):
        return self.binary_op(self.call, (tt_power, ), self.factor)
    
    def factor(self):
        res = ParseResult()
        token = self.current_token
        
        if token.type in (tt_plus, tt_minus):
            res.register_advancement()
            self.advance()
            factor = res.register(self.factor())
            if res.error: return res
            return res.success(UnaryOpNode(token, factor))
        
        
        
        return self.power()
    
    def term(self):
        return self.binary_op(self.factor, (tt_mul, tt_div))
    
    def arith_expr(self):
        return self.binary_op(self.term, (tt_plus, tt_minus))
            
    def comp_expr(self):
        res = ParseResult()
        
        if self.current_token.matches(tt_keyword, 'not'):
            op_token = self.current_token
            res.register_advancement()
            self.advance()
            
            node = res.register(self.comp_expr())
            if res.error: return res
            return res.success(UnaryOpNode(op_token, node))
        
        node = res.register(self.binary_op(self.arith_expr, (tt_ee, tt_ne, tt_lt, tt_gt, tt_lte, tt_gte)))
        
        if res.error:
            return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected int, float, identifier, '+', '-', '(', '[' or 'not'"))
        
        return res.success(node)
            
    def expr(self):
        res = ParseResult()
        
        if self.current_token.matches(tt_keyword, 'var'):
            res.register_advancement()
            self.advance()
            
            if self.current_token.type != tt_identifier:
                return res.fail(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end, "Expected Identifier"
                ))
                
            var_name = self.current_token
            res.register_advancement()
            self.advance()
            
            if self.current_token.type != tt_eq:
                return res.fail(InvalidSyntaxError, self.current_token.pos_start, self.current_token.pos_end, "Expected '='")
            
            res.register_advancement()
            self.advance()
            expr = res.register(self.expr())
            if res.error: return res
            return res.success(VarAssignNode(var_name, expr))
        
        node = res.register(self.binary_op(self.comp_expr, ((tt_keyword, "and"), (tt_keyword, "or"))))
        
        if res.error: return res.fail(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected 'var', 'for', 'while', 'if', 'def', int, float, identifier, '+', '-', '(', '[' or 'not'"))
        
        return res.success(node)
    
    def binary_op(self, func_a, ops, func_b=None):
        if func_b == None:
            func_b = func_a
        res = ParseResult()
        left = res.register(func_a())
        if res.error: return res
        
        while self.current_token.type in ops or (self.current_token.type, self.current_token.value) in ops:
            op_token = self.current_token
            res.register_advancement()
            self.advance()
            right = res.register(func_b())
            if res.error: return res
            left = BinaryOpNode(left, op_token, right)
            
        return res.success(left)
    
##################
# RUNTIME RESULT #
##################

class RTResult:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.value = None
        self.error = None
        self.func_return_value = None
        self.loop_should_continue = False
        self.loop_should_break = False
    
    def register(self, res):
        if res.error: self.error = res.error
        self.func_return_value = res.func_return_value
        self.loop_should_continue = res.loop_should_continue
        self.loop_should_break = res.loop_should_break
        return res.value
    
    def success(self, value):
        self.reset()
        self.value = value
        return self
    
    def success_return(self, value):
        self.reset()
        self.func_return_value = value
        return self
    
    def success_continue(self):
        self.reset()
        self.loop_should_continue = True
        return self
    
    def success_break(self):
        self.reset()
        self.loop_should_break = True
        return self
        
    def fail(self, error):
        self.reset()
        self.error = error
        return self
    
    def should_return(self):
        return (self.error or self.func_return_value or self.loop_should_continue or self.loop_should_break)
    
##########
# VALUES #
##########

class Value:
    def __init__(self):
        self.set_pos()
        self.set_context()
        
    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self
    
    def set_context(self, context=None):
        self.context = context
        return self
    
    def added_to(self, other):
        return None, self.illegal_operation(other)
    
    def subtracted_by(self, other):
        return None, self.illegal_operation(other)
    
    def multiplied_by(self, other):
        return None, self.illegal_operation(other)
    
    def divided_by(self, other):
        return None, self.illegal_operation(other)
    
    def get_comparison_eq(self, other):
        return None, self.illegal_operation(other)
    
    def get_comparison_ne(self, other):
        return None, self.illegal_operation(other)
    
    def get_comparison_lt(self, other):
        return None, self.illegal_operation(other)
    
    def get_comparison_gt(self, other):
        return None, self.illegal_operation(other)
    
    def get_comparison_lte(self, other):
        return None, self.illegal_operation(other)
    
    def get_comparison_gte(self, other):
        return None, self.illegal_operation(other)
    
    def anded_by(self, other):
        return None, self.illegal_operation(other)
    
    def ored_by(self, other):
        return None, self.illegal_operation(other)
    
    def notted(self):
        return None, self.illegal_operation()
    
    def execute(self, args=None):
        return RTResult().fail(self.illegal_operation())
    
    def copy(self):
        raise Exception('No copy method defined')
    
    def is_true(self):
        return False
    
    def illegal_operation(self, other=None):
        if not other: other = self
        return RTError(self.pos_start, other.pos_end, 'Illegal operation', self.context)

class Number(Value):
    def __init__(self, value):
        super().__init__()
        self.value = value
    
    def __repr__(self):
        return str(self.value)
    
    def added_to(self, other):
        if isinstance(other, Number):
            return Number(self.value + other.value).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)
        
    def subtracted_by(self, other):
        if isinstance(other, Number):
            return Number(self.value - other.value).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)
        
    def multiplied_by(self, other):
        if isinstance(other, Number):
            return Number(self.value * other.value).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)
        
    def divided_by(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RTError(other.pos_start, other.pos_end, 'Division by zero', self.context)
            
            return Number(self.value / other.value).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)
        
    def powered_by(self, other):
        if isinstance(other, Number):
            return Number(self.value ** other.value).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)
        
    def get_comparison_eq(self, other):
        if isinstance(other, Number):
            return Number(int(self.value == other.value)).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)
        
    def get_comparison_ne(self, other):
        if isinstance(other, Number):
            return Number(int(self.value != other.value)).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)
        
    def get_comparison_lt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value < other.value)).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)
        
    def get_comparison_gt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value > other.value)).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)
        
    def get_comparison_lte(self, other):
        if isinstance(other, Number):
            return Number(int(self.value <= other.value)).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)
        
    def get_comparison_gte(self, other):
        if isinstance(other, Number):
            return Number(int(self.value >= other.value)).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)
        
    def anded_by(self, other):
        if isinstance(other, Number):
            return Number(int(self.value and other.value)).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)
        
    def ored_by(self, other):
        if isinstance(other, Number):
            return Number(int(self.value or other.value)).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)
        
    def notted(self):
        return Number(1 if self.value == 0 else 0).set_context(self.context), None
        
    def copy(self):
        copy = Number(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy
    
    def is_true(self):
        return self.value != 0
    
    def __repr__(self):
        return str(self.value)
    
Number.null = 0
Number.false = 0
Number.true = 1
    
    
class String(Value):
    def __init__(self, value):
        super().__init__()
        self.value = value
        
    def added_to(self, other):
        if isinstance(other, String):
            return String(self.value + other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)
        
    def multiplied_by(self, other):
        if isinstance(other, Number):
            return String(self.value * other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)
        
    def is_true(self):
        return len(self.value) > 0
    
    def copy(self):
        copy = String(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy
    
    def __str__(self):
        return self.value
    
    def __repr__(self):
        return f'"{self.value}"'
    
class List(Value):
    def __init__(self, elements):
        super().__init__()
        self.elements = elements
        
    def added_to(self, other):
        new_list = self.copy()
        new_list.elements.append(other)
        return new_list, None
    
    def subtracted_by(self, other):
        if isinstance(other, Number):
            new_list = self.copy()
            try:
                new_list.elements.pop(other.value)
                return new_list, None
            except:
                return None, RTError(
                    other.pos_start, other.pos_end, 'Element at this index could not be removed from list because index is out of bounds', self.context
                )
        else:
            return None, Value.illegal_operation(self, other)
    
    def multiplied_by(self, other):
        if isinstance(other, List):
            new_list = self.copy()
            new_list.elements.extend(other.elements)
            return new_list, None
        else:
            return None, Value.illegal_operation(self, other)
        
    def divided_by(self, other):
        if isinstance(other, Number):
            try:
                return self.elements[other.value], None
            except:
                return None, RTError(
                    other.pos_start, other.pos_end, 'Element at this index could not be retrieved from list because index is out of bounds', self.context
                )
        else:
            return None, Value.illegal_operation(self, other)
        
    def copy(self):
        copy = List(self.elements)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy
    
    def __str__(self):
        return ", ".join([str(x) for x in self.elements])
    
    def __repr__(self):
        return f'[{", ".join([str(x) for x in self.elements])}]'
    
class BaseFunction(Value):
    def __init__(self, name):
        super().__init__()
        self.name = name or '<anonymous>'
        
    def generate_new_context(self):
        new_context = Context(self.name, self.context, self.pos_start)
        new_context.symbol_table = SymbolTable(new_context.parent.symbol_table)
        return new_context
    
    def check_args(self, arg_names, args):
        res = RTResult()
        
        if len(args) > len(arg_names):
            return res.fail(RTError(self.pos_start, self.pos_end, f"{len(args) - len(arg_names)} too many arguments passed into '{self.name}'", self.context))
        
        if len(args) < len(arg_names):
            return res.fail(RTError(self.pos_start, self.pos_end, f"{len(arg_names) - len(args)} too few arguments passed into '{self.name}'", self.context))
        
        return res.success(None)
    
    def populate_args(self, arg_names, args, exec_context):
        for i in range(len(args)):
            arg_name = arg_names[i]
            arg_value = args[i]
            arg_value.set_context(exec_context)
            exec_context.symbol_table.set_value(arg_name, arg_value)
            
    def check_and_populate_args(self, arg_names, args, exec_context):
        res = RTResult()
        res.register(self.check_args(arg_names, args))
        if res.should_return(): return res
        self.populate_args(arg_names, args, exec_context)
        return res.success(None)
        
        
    
class Function(BaseFunction):
    def __init__(self, name, body_node, arg_names, should_auto_return):
        super().__init__(name)
        self.body_node = body_node
        self.arg_names = arg_names
        self.should_auto_return = should_auto_return
        
    def execute(self, args):
        res = RTResult()
        interpreter = Interpreter()
        
        exec_context = self.generate_new_context()
        
        res.register(self.check_and_populate_args(self.arg_names, args, exec_context))
        if res.should_return(): return res
            
        value = res.register(interpreter.visit(self.body_node, exec_context))
        if res.should_return() and res.func_return_value == None: return res
        
        return_value = (value if self.should_auto_return else None) or res.func_return_value or Number.null
        return res.success(return_value)
    
    def copy(self):
        copy = Function(self.name, self.body_node, self.arg_names, self.should_auto_return)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy
    
    def __repr__(self):
        return f"<function {self.name}>"
    
class BuiltInFunction(BaseFunction):
    def __init__(self, name):
        super().__init__(name)
        
    def execute(self, args):
        res = RTResult()
        exec_context = self.generate_new_context()
        
        method_name = f'execute_{self.name}'
        method = getattr(self, method_name, self.no_visit_method)
        
        res.register(self.check_and_populate_args(method.arg_names, args, exec_context))
        if res.should_return(): return res
        
        return_value = res.register(method(exec_context))
        if res.should_return(): return res
        
        return res.success(return_value)
        
    def no_visit_method(self, node, context):
        raise Exception(f'No execute_{self.name} method defined')
    
    def copy(self):
        copy = BuiltInFunction(self.name)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy
    
    def __repr__(self):
        return f"<built-in function {self.name}>"
    
    ###############################################
    #                                             #
    #             BUILT-IN FUNCTIONS              #
    #                                             #
    ###############################################
    
    def execute_print(self, exec_context):
        print(str(exec_context.symbol_table.get('value')))
        return RTResult().success(Number.null)
    execute_print.arg_names = ['value']
    
    def execute_print_ret(self, exec_context):
        return RTResult().success(String(str(exec_context.symbol_table.get('value'))))
    execute_print_ret.arg_names = ['value']
    
    def execute_input(self, exec_context):
        text = input()
        return RTResult().success(String(text))
    execute_input.arg_names = []
    
    def execute_input_int(self, exec_context):
        while True:
            text = input()
            try:
                number = int(text)
                break
            except ValueError:
                print(f"'{text}' must be an integer. Try again!")
        return RTResult().success(Number(number))
    execute_input.arg_names = []
    
    def execute_clear(self, exec_context):
        os.system('cls' if os.name == 'nt' else 'clear')
        return RTResult().success(Number.null)
    execute_clear.arg_names = []
    
    def execute_is_number(self, exec_context):
        is_number = isinstance(exec_context.symbol_table.get('value'), Number)
        return RTResult().success(Number.true if is_number else Number.false)
    execute_is_number.arg_names = ['value']
    
    def execute_is_string(self, exec_context):
        is_string = isinstance(exec_context.symbol_table.get('value'), String)
        return RTResult().success(Number.true if is_string else Number.false)
    execute_is_string.arg_names = ['value']
    
    def execute_is_list(self, exec_context):
        is_list = isinstance(exec_context.symbol_table.get('value'), List)
        return RTResult().success(Number.true if is_list else Number.false)
    execute_is_list.arg_names = ['value']
    
    def execute_is_function(self, exec_context):
        is_function = isinstance(exec_context.symbol_table.get('value'), BaseFunction)
        return RTResult().success(Number.true if is_function else Number.false)
    execute_is_function.arg_names = ['value']
    
    def execute_append(self, exec_context):
        list_ = exec_context.symbol_table.get('list')
        value = exec_context.symbol_table.get('value')
        
        if not isinstance(list_, List):
            return RTResult().fail(RTError(self.pos_start, self.pos_end, "First argument must be list", exec_context))
        
        list_.elements.append(value)
        return RTResult().success(Number.null)
    execute_append.arg_names = ['list', 'value']
    
    def execute_pop(self, exec_context):
        list_ = exec_context.symbol_table.get('list')
        index = exec_context.symbol_table.get('index')
        
        if not isinstance(list_, List):
            return RTResult().fail(RTError(self.pos_start, self.pos_end, "First argument must be list", exec_context))
        
        if not isinstance(index, Number):
            return RTResult().fail(RTError(self.pos_start, self.pos_end, "Second argument must be number", exec_context))
        
        try:
            element = list_.elements.pop(index.value)
        except:
            return RTResult().fail(RTError(self.pos_start, self.pos_end, "Element at this index could not be removed from the list because index is out of bounds", exec_context))
        
        return RTResult().success(element)
    execute_pop.arg_names = ['list', 'index']
    
    def execute_extend(self, exec_context):
        listA = exec_context.symbol_table.get('listA')
        listB = exec_context.symbol_table.get('listB')
        
        if not isinstance(listA, List):
            return RTResult().fail(RTError(self.pos_start, self.pos_end, "First argument must be list", exec_context))
        if not isinstance(listB, List):
            return RTResult().fail(RTError(self.pos_start, self.pos_end, "Second argument must be list", exec_context))
        
        listA.elements.extend(listB.elements)
        return RTResult().success(Number.null)
    execute_extend.arg_names = ['listA', 'listB']
    
    def execute_len(self, exec_context):
        list_ = exec_context.symbol_table.get('list')
        
        if not isinstance(list_, List):
            return RTResult().fail(RTError(self.pos_start, self.pos_end, "Argument must be list", exec_context))
        
        return RTResult().success(Number(len(list_.elements)))
    execute_len.arg_names = ['list']
    
    def execute_insert(self, exec_context):
        list_ = exec_context.symbol_table.get('list')
        index = exec_context.symbol_table.get('index')
        value = exec_context.symbol_table.get('value')
        
        list_.elements.insert(index.value, value)
        return RTResult().success(Number.null)
    execute_insert.arg_names = ['list', 'index', 'value']
    
    def execute_replace_index(self, exec_context):
        list_ = exec_context.symbol_table.get('list')
        index = exec_context.symbol_table.get('index')
        value = exec_context.symbol_table.get('value')
        
        list_.elements.pop(index.value)
        list_.elements.insert(index.value, value)
        return RTResult().success(Number.null)
    execute_replace_index.arg_names = ['list', 'index', 'value']
    
    def execute_run(self, exec_context):
        filename = exec_context.symbol_table.get('filename')
        
        if not isinstance(filename, String):
            return RTResult().fail(RTError(self.pos_start, self.pos_end, "Argument must be string", exec_context))
        
        filename = filename.value
        
        try:
            with open(filename, "r") as f:
                script = f.read()
        except Exception as e:
            return RTResult().fail(RTError(self.pos_start, self.pos_end, f'Failed to load script "{filename}"\n' + str(e), exec_context))
        
        _, error = run(filename, script)
        
        if error:
            return RTResult().fail(RTError(self.pos_start, self.pos_end, f'Failed to finish executing script "{filename}"\n' + error.as_string(), exec_context))
        
        return RTResult().success(Number.null)
    execute_run.arg_names = ['filename']
    
    
BuiltInFunction.print = BuiltInFunction('print')
BuiltInFunction.print_ret = BuiltInFunction('print_ret')
BuiltInFunction.input = BuiltInFunction('input')
BuiltInFunction.input_int = BuiltInFunction('input_int')
BuiltInFunction.clear = BuiltInFunction('clear')
BuiltInFunction.is_number = BuiltInFunction('is_number')
BuiltInFunction.is_string = BuiltInFunction('is_string')
BuiltInFunction.is_list = BuiltInFunction('is_list')
BuiltInFunction.is_function = BuiltInFunction('is_function')
BuiltInFunction.append = BuiltInFunction('append')
BuiltInFunction.pop = BuiltInFunction('pop')
BuiltInFunction.extend = BuiltInFunction('extend')
BuiltInFunction.len = BuiltInFunction('len')
BuiltInFunction.insert = BuiltInFunction('insert')
BuiltInFunction.replace_index = BuiltInFunction('replace_index')
BuiltInFunction.run = BuiltInFunction('run')
        
        
###########
# CONTEXT #
###########

class Context:
    def __init__(self, display_name, parent=None, parent_entry_pos=None):
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos
        self.symbol_table = None
        
##########
# SYMBOL #
##########

class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent
        
    def get(self, name):
        value = self.symbols.get(name, None)
        if value == None and self.parent:
            return self.parent.get(name)
        return value
    
    def set_value(self, name, value):
        self.symbols[name] = value
        
    def remove(self, name):
        del self.symbols[name]
        
###############
# INTERPRETER #
###############

class Interpreter:
    def visit(self, node, context):
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, self.no_visit_method)
        return method(node, context)
    
    def no_visit_method(self, node, context):
        raise Exception(f'No visit_{type(node).__name__} method defined')
    
    ###################
    
    def visit_NumberNode(self, node, context):
        return RTResult().success(Number(node.token.value).set_context(context).set_pos(node.pos_start, node.pos_end))
    
    def visit_StringNode(self, node, context):
        return RTResult().success(String(node.token.value).set_context(context).set_pos(node.pos_start, node.pos_end))
    
    def visit_ListNode(self, node, context):
        res = RTResult()
        elements = []
        
        for element_node in node.element_nodes:
            elements.append(res.register(self.visit(element_node, context)))
            if res.should_return(): return res
            
        return res.success(List(elements).set_context(context).set_pos(node.pos_start, node.pos_end))
    
    def visit_VarAccessNode(self, node, context):
        res = RTResult()
        var_name = node.var_name_token.value
        value = context.symbol_table.get(var_name)
        
        if not value:
            return res.fail(RTError(node.pos_start, node.pos_end, f"'{var_name}' is not defined", context))
        
        value = value.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
        return res.success(value)
    
    def visit_VarAssignNode(self, node, context):
        res = RTResult()
        var_name = node.var_name_token.value
        value = res.register(self.visit(node.value_node, context))
        if res.should_return(): return res
        
        context.symbol_table.set_value(var_name, value)
        return res.success(value)
        
    def visit_BinaryOpNode(self, node, context):
        res = RTResult()
        left = res.register(self.visit(node.left_node, context))
        if res.should_return(): return res
        right = res.register(self.visit(node.right_node, context))
        if res.should_return(): return res
        
        if node.op_token.type == tt_plus:
            result, error = left.added_to(right)
            
        elif node.op_token.type == tt_minus:
            result, error = left.subtracted_by(right)
            
        elif node.op_token.type == tt_mul:
            result, error = left.multiplied_by(right)
            
        elif node.op_token.type == tt_div:
            result, error = left.divided_by(right)
            
        elif node.op_token.type == tt_power:
            result, error = left.powered_by(right)
            
        elif node.op_token.type == tt_ee:
            result, error = left.get_comparison_eq(right)
            
        elif node.op_token.type == tt_ne:
            result, error = left.get_comparison_ne(right)
            
        elif node.op_token.type == tt_lt:
            result, error = left.get_comparison_lt(right)
            
        elif node.op_token.type == tt_gt:
            result, error = left.get_comparison_gt(right)
            
        elif node.op_token.type == tt_lte:
            result, error = left.get_comparison_lte(right)
            
        elif node.op_token.type == tt_gte:
            result, error = left.get_comparison_gte(right)
            
        elif node.op_token.matches(tt_keyword, 'and'):
            result, error = left.anded_by(right)
            
        elif node.op_token.matches(tt_keyword, 'or'):
            result, error = left.ored_by(right)
            
        if error:
            return res.fail(error)
        else:
            return res.success(result.set_pos(node.pos_start, node.pos_end))
        
    def visit_UnaryOpNode(self, node, context):
        res = RTResult()
        number = res.register(self.visit(node.node, context))
        if res.should_return(): return res
        
        error = None
        
        if node.op_token.type == tt_minus:
            number, error = number.multiplied_by(Number(-1))
        elif node.op_token.matches(tt_keyword, 'not'):
            number, error = number.notted()
            
        if error:
            return res.fail(error)
        else:
            return res.success(number.set_pos(node.pos_start, node.pos_end))
        
    def visit_IfNode(self, node, context):
        res = RTResult()
        
        for condition, expr, should_return_null in node.cases:
            condition_value = res.register(self.visit(condition, context))
            if res.should_return(): return res
            
            if condition_value.is_true():
                expr_value = res.register(self.visit(expr, context))
                if res.should_return(): return res
                return res.success(Number.null if should_return_null else expr_value)
            
        if node.else_case:
            expr, should_return_null = node.else_case
            else_value = res.register(self.visit(expr, context))
            if res.should_return(): return res
            return res.success(Number.null if should_return_null else else_value)
            
        return res.success(Number.null)
    
    def visit_ForNode(self, node, context):
        res = RTResult()
        elements = []
        
        start_value = res.register(self.visit(node.start_value_node, context))
        if res.should_return(): return res
        
        end_value = res.register(self.visit(node.end_value_node, context))
        if res.should_return(): return res
        
        if node.step_value_node:
            step_value = res.register(self.visit(node.step_value_node, context))
            if res.should_return(): return res
        else:
            step_value = Number(1)
            
        i = start_value.value
        
        if step_value.value >= 0:
            condition = lambda: i < end_value.value
        else:
            condition = lambda: i > end_value.value
            
        while condition():
            context.symbol_table.set_value(node.var_name_token.value, Number(i))
            i += step_value.value

            value = res.register(self.visit(node.body_node, context))
            if res.should_return() and res.loop_should_continue == False and res.loop_should_break == False: return res
            
            if res.loop_should_continue:
                continue
            
            if res.loop_should_break:
                break
            
            elements.append(value)
            
        return res.success(Number.null if node.should_return_null else List(elements).set_context(context).set_pos(node.pos_start, node.pos_end))
    
    def visit_WhileNode(self, node, context):
        res = RTResult()
        elements = []
        
        while True:
            condition = res.register(self.visit(node.condition_node, context))
            if res.should_return(): return res
            
            if not condition.is_true(): break
            
            value = res.register(self.visit(node.body_node, context))
            if res.should_return() and res.loop_should_continue == False and res.loop_should_break == False: return res
            
            if res.loop_should_continue:
                continue
            
            if res.loop_should_break:
                break
            
            elements.append(value)
            
        return res.success(Number.null if node.should_return_null else List(elements).set_context(context).set_pos(node.pos_start, node.pos_end))
    
    def visit_FuncDefNode(self, node, context):
        res = RTResult()
        
        func_name = node.var_name_token.value if node.var_name_token else None
        body_node = node.body_node
        arg_names = [arg_name.value for arg_name in node.arg_name_tokens]
        func_value = Function(func_name, body_node, arg_names, node.should_auto_return).set_context(context).set_pos(node.pos_start, node.pos_end)
        
        if node.var_name_token:
            context.symbol_table.set_value(func_name, func_value)
            
        return res.success(func_value)
    
    def visit_CallNode(self, node, context):
        res = RTResult()
        args = []
        
        value_to_call = res.register(self.visit(node.node_to_call, context))
        if res.should_return(): return res
        value_to_call = value_to_call.copy().set_pos(node.pos_start, node.pos_end)
        
        for arg_node in node.arg_nodes:
            args.append(res.register(self.visit(arg_node, context)))
            if res.should_return(): return res
            
        return_value = res.register(value_to_call.execute(args))
        if res.should_return(): return res
        #return_value = return_value.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
        
        return res.success(return_value)
    
    def visit_ReturnNode(self, node, context):
        res = RTResult()
        
        if node.node_to_return:
            value = res.register(self.visit(node.node_to_return, context))
            if res.should_return(): return res
        else:
            value = Number.null
            
        return res.success_return(value)
    
    def visit_ContinueNode(self, node, context):
        return RTResult().success_continue()
    
    def visit_BreakNode(self, node, context):
        return RTResult().success_break()
        
        
#######
# RUN #
#######

global_symbol_table = SymbolTable()
global_symbol_table.set_value("Null", Number.null)
global_symbol_table.set_value("True", Number.true)
global_symbol_table.set_value("False", Number.false)
global_symbol_table.set_value("print", BuiltInFunction.print)
global_symbol_table.set_value("print_ret", BuiltInFunction.print_ret)
global_symbol_table.set_value("input", BuiltInFunction.input)
global_symbol_table.set_value("input_int", BuiltInFunction.input_int)
global_symbol_table.set_value("clear", BuiltInFunction.clear)
global_symbol_table.set_value("cls", BuiltInFunction.clear)
global_symbol_table.set_value("is_num", BuiltInFunction.is_number)
global_symbol_table.set_value("is_str", BuiltInFunction.is_string)
global_symbol_table.set_value("is_list", BuiltInFunction.is_list)
global_symbol_table.set_value("is_function", BuiltInFunction.is_function)
global_symbol_table.set_value("append", BuiltInFunction.append)
global_symbol_table.set_value("pop", BuiltInFunction.pop)
global_symbol_table.set_value("extend", BuiltInFunction.extend)
global_symbol_table.set_value("len", BuiltInFunction.len)
global_symbol_table.set_value("insert", BuiltInFunction.insert)
global_symbol_table.set_value("replace_index", BuiltInFunction.replace_index)
global_symbol_table.set_value("run", BuiltInFunction.run)


def run(file, text):
    lexer = Lexer(file, text)
    tokens, error = lexer.make_tokens()
    if error: return None, error
    
    parser = Parser(tokens)
    ast = parser.parse()
    if ast.error: return None, ast.error
    
    interpreter = Interpreter()
    context = Context('<program>')
    context.symbol_table = global_symbol_table
    result = interpreter.visit(ast.node, context)
    
    return result.value, result.error

