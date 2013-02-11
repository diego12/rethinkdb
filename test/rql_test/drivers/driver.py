from sys import path
import sys
import types
import pdb
import collections
path.append("../../drivers/python2")

from os import environ
import rethinkdb as r 

JSPORT = int(sys.argv[1])
CPPPORT = int(sys.argv[2])

# -- utilities --

class Lst:
    def __init__(self, lst):
        self.lst = lst

    def __eq__(self, other):
        if len(self.lst) != len(other):
            return False
        
        for i in xrange(len(self.lst)):
            if not (self.lst[i] == other[i]):
                return False

        return True

    def __repr__(self):
        return repr(self.lst)

class Bag(Lst):
    def __init__(self, lst):
        self.lst = sorted(lst)

    def __eq__(self, other):
        other = sorted(other)

        if len(self.lst) != len(other):
            return False
        
        for i in xrange(len(self.lst)):
            if not (self.lst[i] == other[i]):
                return False

        return True

class Dct:
    def __init__(self, dct):
        self.dct = dct
    
    def __eq__(self, other): 
        for key in self.dct.keys():
            if not key in other.keys():
                return False
            if not (self.dct[key] == other[key]):
                return False
        return True

    def __repr__(self):
        return repr(self.dct)

# -- Curried output test functions --

def eq(exp):
    if isinstance(exp, list):
        exp = Lst(exp)
    elif isinstance(exp, dict):
        exp = Dct(exp)

    def sub(val):
        if not (val == exp):
            print "Equality comparison failed"
            print "Value:", repr(val), "Expected:", repr(exp)
            return False
        else:
            return True
    return sub

class PyTestDriver:

    # Set up connections to each database server
    def connect(self):
        print 'Connecting to JS server on port ' + str(JSPORT)
        self.js_conn = r.connect(host='localhost', port=JSPORT)
        print 'Connecting to CPP server on port ' + str(CPPPORT)
        self.cpp_conn = r.connect(host='localhost', port=CPPPORT)
        self.scope = {}

    def define(self, expr):
        exec(expr, globals(), self.scope)

    def run(self, src, expected, name):
        try:
            query = eval(src, dict(globals().items() + self.scope.items()))
        except Exception as err:
            print name, "- Python error on construction of query:", str(err)
            return

        exp_fun = eval(expected, dict(globals().items() + self.scope.items()))
        if not isinstance(exp_fun, types.FunctionType):
            exp_fun = eq(exp_fun)

        try:
            cppres = query.run(self.cpp_conn)
            if not exp_fun(cppres):
                print " in CPP version of:", name, src
        except Exception as err:
            print name, "- Error on running of query on CPP server:", str(err)

        try:
            jsres = query.run(self.js_conn)
            if not exp_fun(jsres):
                print " in JS version of:", name, src
        except Exception as err:
            print name, "- Error on running of query on JS server:", str(err)

driver = PyTestDriver()
driver.connect()

# Emitted test code will consist of calls to this function
def test(query, expected, name):
    driver.run(query, expected, name)

# Emitted test code can call this function to define variables
def define(expr):
    driver.define(expr)

# Emitted test code can call this function to set bag equality on a list
def bag(lst):
    return Bag(lst)

