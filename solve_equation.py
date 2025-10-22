import string
letters = string.ascii_letters
digits = '0123456789'

class Node_token:
    def __init__(self, data):
        self.data = data
        self.next = None
    def __repr__(self):
        return str(self.data)

class LinkedList:
    def __init__(self):
        self.head = None
        self.current = None
        self.data = ''
        self.routes = {}

    def __repr__(self):
        elements = []
        current = self.head
        while current is not None:
            elements.append(repr(current.data))
            current = current.next
        return " -> ".join(elements)

    def __iter__(self):
        self.currentIndex=self.head
        return self
    def __next__(self):
        if self.currentIndex:
            data=self.currentIndex.data
            self.currentIndex=self.currentIndex.next
            return data
        else:
            raise StopIteration
    def add_last(self, data):
        new_node = Node_token(data)
        self.data += f"data:{new_node.data} ==> "
        if self.head is None:
            self.head = new_node
            self.current = new_node
            return
        self.current.next = new_node
        self.current = new_node

    def route(self, path):
        def wrapper(func):
            self.routes[path] = func
            return func
        return wrapper

    def handle_request(self, path):
        if path in self.routes:
            response = self.routes[path]()
            print(response)
        else:
            print("404 Not Found")


class Token:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value
    def __repr__(self):
        return f'({self.type}:{self.value})'


class Lexer:
    def __init__(self, text):
        self.text = text
        self.tokens = LinkedList()
        self.currentIndex = -1
        self.currentChar = None
        self.pre = None
        self.advanced()

    def advanced(self):
        self.currentIndex += 1
        if self.currentIndex < len(self.text):
            self.pre = self.currentChar
            self.currentChar = self.text[self.currentIndex]
        else:
            self.currentChar = None

    def make_number(self):
        number = ''
        while self.currentChar is not None and self.currentChar in digits + '.':
            number += self.currentChar
            self.advanced()
        return Fraction(float(number))

    def make_string(self):
        s = ''
        while self.currentChar is not None and self.currentChar in letters + digits:
            s += self.currentChar
            self.advanced()
        return s

    def tokenize(self):
        while self.currentChar is not None:
            if self.currentChar in " \t":
                self.advanced()
            

            elif self.currentChar in digits:
                self.tokens.add_last(Token("NUMBER", self.make_number()))
            elif self.currentChar in letters:
                self.tokens.add_last(Token("WORD", self.make_string()))
            elif self.currentChar == '+':
                self.tokens.add_last(Token('PLUS', '+'))
                self.advanced()
            elif self.currentChar == '-':
                self.tokens.add_last(Token('MINUS', '-'))
                self.advanced()
            elif self.currentChar == '(':
                self.tokens.add_last(Token('LB', '('))
                self.advanced()
            elif self.currentChar == ')':
                self.tokens.add_last(Token('RB', ')'))
                self.advanced()
            elif self.currentChar == '=':
                self.tokens.add_last(Token('Equal', '='))
                self.advanced()
            elif self.currentChar == ';':
                while self.currentChar == ';':
                    self.advanced()
                    if self.currentChar is None:
                        break
                # نتأكد إننا مش في نهاية النص
                if self.currentChar is not None or self.pre != ';':
                    self.tokens.add_last(Token("EOE", ";"))

            else:
                raise Exception(f"Invalid token {self.currentChar}")

        self.tokens.add_last(Token("EOE", ";"))
        return self.tokens


class Node:
    def __init__(self, data):
        self.data = data
    def __repr__(self):
        return repr(self.data)



class Parser:
    def __init__(self, tokens: LinkedList):
        self.tokens = tokens
        self.current = self.tokens.head
        self.equations = []
        self.current_eq = []
        self.current_sign = 1
        self.current_row = 0

    def advanced(self):
        if self.current.next is not None:
            self.current = self.current.next
        else:
            self.current = None

    def parser(self):
        while self.current is not None:
            token = self.current.data
            if token.type == "NUMBER":
                value = token.value
                self.advanced()
                if self.current and self.current.data.type == "WORD":
                    var = self.current.data.value
                    self.current_eq.append((var, value * self.current_sign))
                    self.advanced()
                else:
                    self.current_eq.append(("CONST", value * self.current_sign))
            elif token.type == "WORD":
                var = token.value
                self.current_eq.append((var, 1 * self.current_sign))
                self.advanced()
            elif token.type == "PLUS":
                self.current_sign = 1
                self.advanced()
            elif token.type == "MINUS":
                self.current_sign = -1
                self.advanced()
            elif token.type == "Equal":
                self.current_eq.append(("EQUAL", "="))
                self.current_sign = 1
                self.advanced()
            elif token.type == "EOE":
                if self.current_eq:
                    self.equations.append({
                        "row": self.current_row,
                        "data": self.current_eq.copy()
                    })
                    self.current_eq.clear()
                    self.current_row += 1
                self.advanced()
            else:
                self.advanced()
        return self.equations


class VarList:
    def __init__(self):
        self.addresses = {}

    def append(self, var_name, place, value):
        if var_name not in self.addresses:
            self.addresses[var_name] = {}
        if place in self.addresses[var_name]:
            self.addresses[var_name][place] += value
        else:
            self.addresses[var_name][place] = value
    def __repr__(self):
        return "\n".join([f"{var}: {places}" for var, places in self.addresses.items()])

class Interpreter:
    def __init__(self, parser_output):
        self.vars = VarList()
        self.equations = parser_output
    def __repr__(self):
        return f"{self.vars}"
    def exqution(self):
        for i in self.equations:
            num_equation = i['row']
            after_equal = 1
            for j in i["data"]:
                if j[1] == "=":
                    after_equal = 0
                else:
                    if j[0] !="CONST":
                        if after_equal:
                            self.vars.append(j[0], num_equation, j[1])
                        else:
                            self.vars.append(j[0], num_equation, -j[1])
                    else:
                        if after_equal:
                            self.vars.append(j[0], num_equation, -j[1])
                        else:
                            self.vars.append(j[0], num_equation, j[1])
        return self.vars

   
from math import gcd

class Fraction:
    def __init__(self, numerator, denominator=None):
        if denominator is None:
            if isinstance(numerator, Fraction):
                self.numerator = numerator.numerator
                self.denominator = numerator.denominator
                return

            if isinstance(numerator, (float, str)):
                s = str(numerator)
                if '.' in s:
                    digits = len(s.split('.')[1])
                    num = int(s.replace('.', ''))
                    den = 10 ** digits
                    common = gcd(num, den)
                    self.numerator = num // common
                    self.denominator = den // common
                    return
                else:
                    numerator = int(s)
                    denominator = 1

            if isinstance(numerator, int):
                denominator = 1
            else:
                raise TypeError("Unsupported type for numerator")

        if denominator == 0:
            raise ValueError("Denominator cannot be zero.")

        if denominator < 0:
            numerator *= -1
            denominator *= -1

        common = gcd(abs(numerator), abs(denominator))
        self.numerator = numerator // common
        self.denominator = denominator // common

    def __repr__(self):
        return f"{self.numerator}/{self.denominator}" if self.denominator != 1 else f"{self.numerator}"

    def to_float(self):
        return self.numerator / self.denominator
    def __radd__(self,other):
        return self.__add__(other)
    def __add__(self, other):
        other = Fraction(other)
        new_num = self.numerator * other.denominator + other.numerator * self.denominator
        new_den = self.denominator * other.denominator
        return Fraction(new_num, new_den)
    
    def __neg__(self):
        return Fraction(-self.numerator,self.denominator)
    
    def __rmul__(self, other):
        return self.__mul__(other)

    def __mul__(self, other):
        if isinstance(other,Fraction):
            
            return Fraction(self.numerator * other.numerator, self.denominator * other.denominator)
        elif isinstance(other,(int)):
            return Fraction(self.numerator*other,self.denominator)
        elif isinstance(other,float):
            other=Fraction(other)
            return Fraction(self.numerator * other.numerator, self.denominator * other.denominator)
    def __truediv__(self, other):
        if isinstance(other,Fraction):
            return Fraction(self.numerator * other.denominator, self.denominator * other.numerator)
        elif isinstance(other, (int, float)):
            other = Fraction(other)
            return self / other
        else:
            raise "other is invalid type"
    def __eq__(self, other):
        if isinstance(other,Fraction):
            other = Fraction(other)
            return self.numerator == other.numerator and self.denominator == other.denominator
        else:
            return self.to_float()==other

    def is_zero(self):
        return self.numerator == 0
    
def MakeList(inputs: VarList):
    deta = {
        "vars": [],
        "matrix": []
    }

    # استخراج أسماء المتغيرات (ماعدا CONST)
    for var_name in inputs.addresses:
        if var_name != "CONST":
            deta["vars"].append(var_name)

    # ✅ ما نعملش sort علشان نحافظ على ترتيب الإدخال
    # deta["vars"].sort()

    # حساب عدد الصفوف والأعمدة
    num_rows = max(max(places.keys()) for places in inputs.addresses.values()) + 1
    num_cols = len(deta["vars"]) + 1  # زائد عمود للثابتات

    deta["matrix"] = [[Fraction(0) for _ in range(num_cols)] for _ in range(num_rows)]

    # تعبئة المصفوفة بالقيم
    for var_name, places in inputs.addresses.items():
        for row_index, value in places.items():
            if var_name == "CONST":
                deta["matrix"][row_index][-1] = value  # آخر عمود للثابتات
            else:
                col_index = deta["vars"].index(var_name)
                deta["matrix"][row_index][col_index] = value

    return deta

def makeReducedRowEshlon(current,matrix,printed):
    if current < 0:
        return
    pivot = matrix[current][current]
    # نريد جعل العناصر أعلاه صفرًا
    for r in range(current):
        factor = -matrix[r][current] / pivot  # نستخدم القسمة على المحور الرئيسي
        if not factor.is_zero():
            for j in range(len(matrix[current])):
                matrix[r][j] = matrix[r][j] + factor * matrix[current][j]
            printed.add_last(f"<hr> eliminated row {r+1} using row {current+1}, matrix now {matrix}")
    makeReducedRowEshlon(current-1,matrix,printed)
def gaussian_elimination(input_matrix,printed):
    
    printed.add_last(f"the ominted Matrix is {input_matrix["matrix"]} and the variable is {input_matrix['vars']}")
    current=0
    solve(current,input_matrix["matrix"],printed)
    current=len(input_matrix["matrix"])-1
    printed.add_last("<hr> now we make the matrix reduced Row Eshlon Form")
    makeReducedRowEshlon(current,input_matrix["matrix"],printed)
    return printed
def solve(current,matrix,printed):
    if(current==len(matrix)):
        return
    else:
        makeleading(current,matrix,printed)
        makeRowEshlon(current,matrix,printed)
        
        current+=1 
        solve(current,matrix,printed)
        
        
def  makeRowEshlon(current,matrix,printed):
    for i in range(current+1,len(matrix)):
        minsed=-matrix[i][current]
        if minsed!=0:
            for j in range(len(matrix[current])):

                matrix[i][j]=minsed*matrix[current][j]+matrix[i][j]
            printed.add_last(f"<hr>we will multiply row number {i+1} with the number under leading to get {minsed} and we multibly with the row number {current} to be Row Eshlon Form and th current updated of Ominted matrix is {matrix}")
def makeleading(current,matrix,printed):
    if matrix[current][current]==1:
        return
    for i in range(current,len(matrix)):
        if(matrix[i][current]==1):
            matrix[current],matrix[i]=matrix[i],matrix[current]
            printed.add_last(f"<hr> we will change the place of Rows {i+1} and {current+1} <br> and the matrix is {matrix}")
            return
    if matrix[current][current]!=1:
        divided=Fraction(1)/matrix[current][current]
        for i in range(len(matrix[current])):
            matrix[current][i]=matrix[current][i]*divided
        printed.add_last(f"<hr> we will multiblay the row number {current+1} to {divided} to return the {matrix}")
            
def run(equations:str):
    
    print(equations)
    lexer = Lexer(equations)
    tokens = lexer.tokenize()
    print(tokens)
    parser = Parser(tokens)
    equations = parser.parser()
    print(equations)
    interp = Interpreter(equations).exqution()
    listMatrix=MakeList(interp)
    printed=LinkedList()
    
    return gaussian_elimination(listMatrix,printed)
    

