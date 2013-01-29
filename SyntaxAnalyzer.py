#!/usr/bin/python
from pycparser import c_parser, c_ast, parse_file
from clueUtils import *

import sys
import math
import os
import sys
import os.path

# Line numbers here would help ;-)

# TO DOs: 
#  Check each function with return type a pointer to see if dynamic memory was allocated for that pointer 
#  within the function's body 
# 
#  Exception to assigning a constant other than NULL to a pointer: Line 527?
#    assigning a const string like "Hello" to a char * variable 
#  For now: just get rid of this check; very rare that any student would assign a regular constant

tutorialdir = '/clue/Tutorials' 
basepath = tutorialdir+os.sep+'utils'
fakesPath = '%s%sfake_libc_include' %(basepath,os.sep)
logdir = '/clue/analyzerLogs'

if not os.path.exists(logdir):
    os.mkdir(logdir)

#FUTURE: extend malloc to allocators
allocators = ['malloc','calloc','strdup'] # Even though I strongly advise against use of strdup in elementary programming
testerOps = ['If','While','DoWhile','For']

# Portable cpp path for Windows and Linux/Unix
CPPPATH = '%s%scpp.exe' %(basepath,os.sep) if sys.platform == 'win32' else 'cpp'


def getAST(filename): #basename = appdir\\Tutorials\\utils
    ast = None
    ast = parse_file(filename, use_cpp=True,
            cpp_path=CPPPATH, 
            cpp_args='-I/clue/Tutorials/utils/fake_libc_include')
    myFile = open(filename)
    numlines = len(myFile.readlines())
    myFile.close()
    return ast, numlines

def getWarnings(filename):
    ast, numlines = getAST(filename)
    v = smatchVisitor()
    v.generic_visit(ast)
    myFile = open(filename)
    numlines = len(myFile.readlines())
    myFile.close()
    return v.displayWarnings(numlines)

def getWarnings2(ast,numlines):
    v = smatchVisitor()
    v.generic_visit(ast)
    return v.displayWarnings(numlines)

def className(node=None):
    if node == None:
        return None
    else:
        return node.__class__.__name__

def getVarType(node):
    """ This function returns a vdecl object representing the same c variable
        as the subtree rooted at node.
        
        node should be of decl type.
    """
    if node == None:
        print "Grave error:  I tried to get operands for a bad node at %s" % node.coord.line
    else:
        temp = vdecl()
        nodeType = className(node)
        if nodeType == 'Decl':
            t = node.type
            if t != 'FuncDecl':
                temp.modifiers.append([])
	 	# and ... is a blind addition in response to an error
                while className(t) != 'TypeDecl' and className(t) != 'Struct':  
                    if className(t) == 'PtrDecl':
                        temp.pdepth += 1
                        if t.quals != None:
                            temp.modifiers.append(t.quals)
                        else:
                            temp.modifiers.append([])
                    t = t.type
                if className(t) == 'Struct':
                    temp.base = t.name
                elif className(t.type) == 'Struct':
		    temp.base = t.type.name
                    temp.modifiers[0] = t.quals
		else:
		    temp.base = t.type.names[0]
                    temp.modifiers[0] = t.quals
                return temp
            else:
                temp.makeFunction()
        elif nodeType == "FuncDecl":
            pass

class vdecl():
    """ For recording the type of variable declared in the c file.  Can
        handle all basic types and pointers, can be extended easily to
        record modifiers like const or extern.
    """
    def __init__(self, type=None):
        self.pdepth = 0
        self.base = type  # if isStruct is true, this is the struct's name
        self.modifiers = []
        self.isFunction = False
        self.isStruct = False
        
    def isPointer(self):
        if self.pdepth == 0:
            return False
        else:
            return True
            
    def isType(self, type):
        if type == None:
            print "ERROR:  I need a type to check!"
        else:
            return self.base == type
            
    def isConst(self):
        if 'const' in self.modifiers[0]:
            return True
        else:
            return False

    def isExtern(self):
        if 'extern' in self.modifiers[0]:
            return True
        else:
            return False
            
    def makeParameter(self):
        self.modifiers[0].append("Parameter")
        
    def makeFunction(self):
        self.isFunction = True

    def makeStruct(self):
        self.isStruct = True
        
    def isParameter(self):
        if "Parameter" in self.modifiers[0]:
            return True
        else:
            return False
            
    def display(self):
        print "Level of pointers:  %s" %self.pdepth
        structtype = 'struct ' if self.isStruct else ''
        print "Base type:  %s%s" %(structtype,self.base)
        for i in range(len(self.modifiers)):
            part1 = "Modifiers at base level: " if i == 0 else "Modifiers at %sth level of indirection: " % i
            print part1+'     '.join(self.modifiers[i])
        print ""
        
                
            
class scope():
    """ A fancy stack for keeping track of the current scope in the
        program.  As each new code block is entered, a new scope is pushed
        onto the scope stack.  Each new scope stack is a copy of the previous,
        which ensures proper variable scope behavior and restoration
        of the previous scope whenever a code block is exited.
        
        The stack itself is fancy list of dictionaries with some
        fancy methods for manipulations.    
        
        scopeNode[] is a list of nodes.
        scope[] is a list of dictionaries.

        len(scopeNode) = len(scope), invariantly. If not, we have a problem.
    """
    def __init__(self):
        self.scope = []
        self.scope.append({})
        self.scopeNode = []
        self.scopeNode.append(None)
        #f.addScript("hello-version.py")

    def enterScope(self, node):
        self.scopeNode.append(node)
        self.scope.append(dict(self.scope[-1]))

    def exitScope(self):
        self.scope.pop()
        self.scopeNode.pop()
        
    #unused
    def currentScopeNode(self):
        if self.scopeNode == []:
            print "Error... not currently in any scope (?)!"
        else:
            return className(self.scopeNode[-1])

    def currentScope(self):
        if self.scope == []:
            print "Error... not currently in any scope (?)!"
        else:
            return self.scope[-1]
    
    def declare(self, ID, obj):
        self.scope[-1][ID] = obj

    def len(self):
        return len(self.scope)
            
    def isInScope(self,ID):
        if ID in self.scope[-1]:
            return True
        else:
            return False
            
    def ctype(self, ID):
        if self.isInScope(ID):
            return (self.scope[-1])[ID]
        else:
            print "Error!  Object requested (%s) not found in current scope!" %ID
            self.display()
            
    def display(self):
        if len(self.scope) == 1:
            print "No scopes, yet..."
            return
        else:
            print "Number of scopes:" , len(self.scope), "Number of scope nodes:",len(self.scopeNode)
            print [className(i) for i in self.scopeNode]
            print "Current scopes:"
            for i in range(len(self.scope)):
                print "Scope %s:" %(className(self.scopeNode[i]))
                for ID,TYPE in self.scope[i].iteritems():
                    print str(ID)
                print "\n"


class warnings():
    """ This encapsulates the functionality we require to record,
        manipulate, organize, and print the common runtime errors
        we encounter in the students' code.
    """
    def __init__(self, list=[]):
        self.list = list
        
    def append(self, tuple=(-1,'There\'s a bad append somewhere...')):
        self.list.append(tuple)
        
    def isEmpty(self):
        return self.count() == 0
        
    def isNotEmpty(self):
        return self.count() > 0
        
    def sort(self, key='line'):
        if key == 'line':
            self.list = sorted(self.list, key=lambda warning: warning[0])
        elif key == 'error':
            self.list = sorted(self.list, key=lambda warning: warning[1])
        else:
            print "No way for me to sort all these many common mistakes!"
            
    def count(self):
        return len(self.list)
        
    def display(self, numPadding = 100):
        retString = ''
        printStr = "%" + str(int(math.log10(numPadding))+2) + "s:  %" + "s\n"
        self.list.sort()
        for i in self.list:
            retString += printStr % (i[0], i[1])
        return retString


class mallocState():
    def __init__(self):                 # COMMENTS BELOW ADDED BY RT
        self.pointersToBlock = {}       # keys:   integers representing addresses returned by calls to a dynamic memory allocator
                                        #         that address may be NULL or the starting address of an allocated block of dynamic memory
    # Initialize pointersToBlock["0"] = [] and reserve for NULL pointers?
                                        # values: list of pointer variable IDs having target address represented by the key
        self.pointerTarget = {}         # keys are pointer variable IDs, value is the integer representing the target address assigned
                                        # to the pointer
        self.mallocUntested = []        # list of IDs for pointer variables that have not been tested for NULL after call to malloc, ...
    # If above, initialize mallocNum = 1
        self.mallocNum = 0              # Next available dynamic memory block number
        self.mallocUnwarned = []        # List of malloc block numbers for which a warning has not been issued   ## WHAT KIND OF WARNING???
        self.mallocWarned = []          # List of malloc block IDs for which a warning has been issued.  Never shrinks.
        self.checkingForMalloc = True   # How used? Good question. Let me get back to you on that.
        
    def malloc(self, PID):
        self.pointersToBlock[self.mallocNum]=[PID]
        self.pointerTarget[PID] = self.mallocNum
        self.recentMalloc = self.mallocNum
        self.mallocUntested.append(self.mallocNum)
        self.mallocUnwarned.append(self.mallocNum)
        self.mallocNum += 1   # Because of this, cannot reuse freed block numbers
        
    def warn(self, MID):
        if MID in self.mallocUnwarned:
            self.mallocUnwarned.remove(MID)
            self.mallocWarned.append(MID)
        
    def free(self, PID):
        if self.allocatorCalledFor(PID):
            self.warn(self.pointerTarget[PID])  # ???
            dynamicBlockNum=self.pointerTarget[PID] 
            self.pointersToBlock[dynamicBlockNum].remove(PID)
            if len(self.pointersToBlock[dynamicBlockNum]) > 0:
                return False, self.pointersToBlock[dynamicBlockNum]
            else:
                del self.pointersToBlock[dynamicBlockNum]
                del self.pointerTarget[PID]
                return True,[]
        else:
            print "Error!  Trying to free memory not dynamically allocated."
            return False, []
            
    # so far unused
    def untestedPointerCount(self):
        return len(self.mallocUntested)

    def isTested(self, PID):
        if self.allocatorCalledFor(PID) and self.pointerTarget[PID] not in self.mallocUntested:
            return True
        return False
        
    def isWarned(self, MID):
        return True if MID in self.mallocWarned else False

    def setTested(self, PID):
        if self.allocatorCalledFor(PID):
            if self.pointerTarget[PID] in self.mallocUntested:
                self.mallocUntested.remove(self.pointerTarget[PID])
            if self.pointerTarget[PID] in self.mallocUnwarned:
                self.mallocUnwarned.remove(self.pointerTarget[PID])

    def allocatorCalledFor(self, PID):
        if PID in self.pointerTarget:
            return True
        else:
            return False
            
    def isMemoryLeak(self):             # ????
        if self.pointersToBlock != {}:
            return True
        return False
    
    def assign(self, pointA, pointB):
        OK = True
        if pointA in self.pointerTarget:
            blockA = self.pointerTarget[pointA]
            self.pointersToBlock[blockA].remove(pointA)
            if self.pointersToBlock[blockA] == []:     #MEMORY LEAK CAUSED BY ASSIGNMENT TO pointA
                OK = False
        self.pointerTarget[pointA] = self.pointerTarget[pointB]
        self.pointersToBlock[self.pointerTarget[pointA]].append(pointA)
        return OK

    def assignNull(self, pointA):
        OK = True
        if pointA in self.pointerTarget:
            blockA = self.pointerTarget[pointA]
            self.pointersToBlock[blockA].remove(pointA)
            if self.pointersToBlock[blockA] == []:     #MEMORY LEAK CAUSED BY ASSIGNMENT TO pointA
                OK = False
        self.nullPtrs.append(pointA)
        return OK
    
    def display(self, msg = None):
        if msg == None:
            print "Dynamic memory status:\nUnwarned block IDs: %s\nCurrent malloc number: %s"%(self.mallocUnwarned,self.mallocNum)
        else:
            print "Dynamic memory status %s:\nUnwarned block IDs: %s\nCurrent malloc number: %s"%(msg,self.mallocUnwarned,self.mallocNum)
        if len(self.pointersToBlock.items()) == 0:
            print "No dynamically allocated memory blocks..."
        else:
            print "Block number\t\tPointing here:\t\t\tChecked?\t\t\t\tWarned?"
            print "----------------------------------------------------------------------------------------"
            for p,q in self.pointersToBlock.items():
                print "%s\t\t\t\t\t%s\t\t\t\t\t%s\t\t\t\t\t%s" %(p,q,self.isTested(q[0]),self.isWarned(p))
            print ""


class smatchVisitor(c_ast.NodeVisitor):

    def __init__(self,stack=[]):
        self.danglingPtrs = []
        self.nullPtrs = []
        self.warnings = warnings([]) # BIZARRE - apparently if we don't pass in [], list from previous call retained!
        self.nodeStack = []
        self.scopeStack = scope()
        self.dynaMem = mallocState()
        self.branchTaken = []   # This is a stack that corresponds to the name of the childnode pointer traversed;
                                # A stack that corresponds to nodestack.
                                # IE branchTaken[i] gives the name of the childnode instance variable the visitor took
                                # ...leaving node self.nodeStack[i] to arrive at node self.nodeStack[i+1]
                                # If it is only one such node in a list of nodes, it returns the name of the list

    def topName(self):
        top = self.nodeStack[-1]
        if top != None:
            return className(top)
        else:
            return 'None'

    def inConditional(self,node):
        for i in range(len(self.nodeStack)-1):
            if className(self.nodeStack[i]) in testerOps:
                if self.nodeStack[i+1] == self.nodeStack[i].cond:
                    return True
        return False 

    def show_stack(self):
        for i in range(1,len(self.nodeStack)):
            print className(self.nodeStack[i]) + ' ',
        print ''

    def descendantOf(self,cname):
        if cname in [className(n) for n in self.nodeStack]:
            return True
        else:
            return False

    def closestAncestor(self,cname):
        nameStack = [className(n) for n in self.nodeStack]
        if cname in nameStack:
            topmostIndex = namestack.index(cname)-len(self.nodeStack) # so nameStack[-topmostIndex] == cname
            return self.stack[topmostIndex]
        else:
            return None
            
    def descendantOfBranch(self, tname):
        if tname in [n for n in self.branchTaken]:
            return True
        else:
            return False
        
    def checkStmt(self, stmt = None):
        """ This method is called on individual statements, such as would
            be in the stmts subtree of a compound node or in labels
            such as cases.  Technically, the argument passed should not be
            a list.
        """
        if stmt == None:
            self.warnings.append((node.coord.line, 'Empty statement'))
        else:
            # Put our statement-specific warnings here
            if stmt.__class__.__name__ == 'Constant' or stmt.__class__.__name__ == 'ID':
                self.warnings.append((stmt.coord.line, 'Statement has no effect'))

    def displayWarnings(self, buff=None):
        """ This method simply calls the warnings
            class's display method.        
        """
        return self.warnings.display(buff)  # return self.

    def generic_visit(self, node):
        """ Called if no explicit visitor function exists for a 
            node. Implements preorder visiting of the node.
        """
        if node != None:
            self.nodeStack.append(node)
            #self.show_stack()
            for i in range(len(node.children())):
                self.branchTaken.append('unknown')
                self.visit(node.children()[i])
                self.branchTaken.pop()
            self.nodeStack.pop()
        
    def generic_visit_enter(self,node):
        self.nodeStack.append(node)
        
    def generic_visit_exit(self):
        self.nodeStack.pop()

    def generic_visit_part(self, nodeList=None, nodeType=None):
        """ This is/was mainly called whenever we wanted to visit one list of children
            for a node that had logically distinct lists of children (compound nodes
            used to be this way with decls and stmts)
        """
        if nodeList == None:
            return
        else:
            for node in nodeList:
                self.branchTaken.append('unknown' if nodeType == None else nodeType)
                self.visit(node)
                self.branchTaken.pop()

    def visit_Assignment(self,node):
        """ This is what a visitor node executes when it reaches
            an assignment node in the tree.        
        """
        # Just some error checking
        if node == None:
            print 'None passed as node in visit_Assignment'
            return
        if node.op == '=':
            if className(node.lvalue) == 'ID' and self.scopeStack.ctype(node.lvalue.name).isPointer():
                if className(node.rvalue) == 'ID' and  self.scopeStack.ctype(node.rvalue.name).isPointer():
                    if not self.dynaMem.assign(node.lvalue.name,node.rvalue.name):
                        self.warnings.append((node.coord.line,'Pointer assignment causes memory leak'))
                    if node.rvalue.name in self.nullPtrs:
                        self.nullPtrs.append(node.lvalue.name)
                    else:
                        if node.lvalue.name in self.nullPtrs:
                            self.nullPtrs.remove(node.lvalue.name)
                if className(node.rvalue) == 'FuncCall' or (className(node.rvalue) == 'Cast' and className(node.rvalue.expr) == 'FuncCall'):
                    if node.lvalue.name in self.nullPtrs:  
                        self.nullPtrs.remove(node.lvalue.name)
                    elif node.lvalue.name in self.dynaMem.pointerTarget:
                        blockA = self.pointerTarget[pointA]
                        self.pointersToBlock[blockA].remove(pointA)
                        if self.pointersToBlock[blockA] == []:
                            self.warnings.append((node.coord.line,'Pointer assignment causes memory leak'))
                    
                if className(node.rvalue) == 'Constant':
                    if node.rvalue.value == '0':
                        if not self.dynaMem.assignNull(node.lvalue.name):
                            self.warnings.append((node.coord.line,'Pointer assignment causes memory leak'))
                    else:
                        self.warnings.append((node.coord.line,'Pointer variable assigned constant value other than NULL'))
        else:
            print("Error processing this assignment node... What other kind of operator can an assignment have besides '='?!")
                
        if self.inConditional(node) and className(node.rvalue) != "FuncCall":
            self.warnings.append((node.coord.line,'Possible use of = for == in condition'))

        # the reference to StructRef below was added to enable script to run; must deal with StructRef's separately?
                  
        if className(node.lvalue) != 'UnaryOp' and className(node.lvalue) != 'ArrayRef' and className(node.lvalue) != 'StructRef':
            try:
                isparam = self.scopeStack.ctype(node.lvalue.name).isParameter()
            except:
                print className(node), className(node.lvalue), node.lvalue.name
                sys.exit()
                
            if isparam:
                self.warnings.append((node.coord.line,'Assignment to parameter in function body'))
        else:
            pass
        
        self.generic_visit(node)
                
    def visit_BinaryOp(self,node):
        """ This is what a visitor node executes when it reaches
            a binary operation node in the tree.  Many common errors
            might possibly occur here, because there are so many
            binary operations.        
        """
        if node == None:
            print 'None passed as node in visit_BinaryOp'
            return
        self.generic_visit_enter(node)
        self.generic_visit_part([node.left, node.right])
        if node.op in ['&','|']:
            if self.inConditional(node) and not self.topName() == 'Assignment':  
                self.warnings.append((node.coord.line,'Possible use of %s for %s%s' %(node.op,node.op,node.op)))
        # The true branch is for those equality comparisons
        if node.op in [ '==', '!=' ]:
            # If comparing against any of the many flavors of NULL:
            if (className(node.right) == "ID" and\
                node.right.name in ["NULL",'0']) or\
                (className(node.right) == "Constant" and\
                node.right.value == '0'):
                # If the left operand is a pointer pointing to an allocated block of memory, mark that pointer/block as tested
                #MN: ( p == NULL ) or ( p == 0 )
                if className(node.left) == "ID" and self.dynaMem.allocatorCalledFor(node.left.name):
                    self.dynaMem.setTested(node.left.name)
                # The following catches some forms of immediate comparison after an allocation
                # ((p=malloc(...)) == NULL) or ((p=malloc(...)) == 0 )
                elif className(node.left) == "Assignment" and\
                     className(node.left.lvalue) == "ID" and\
                     className(node.left.rvalue) == "FuncCall" and\
                     node.left.rvalue.name.name in allocators:
                    self.dynaMem.setTested(node.left.lvalue.name)
            # If comparing against any of the many flavors of NULL, this time NULL on the left...
            elif (className(node.left) == "ID" and\
                 node.left.name in ["NULL", '0']) or\
                 (className(node.left) == "Constant" and\
                    node.left.value == '0'):                                
                if className(node.right) == "ID" and\
                   self.dynaMem.allocatorCalledFor(node.right.name):
                    self.dynaMem.setTested(node.right.name)                 #MN: ( NULL/0 == p )
            else: # ADDED BY RT 7/25/2010
                if  className(node.right) == "ID" and\
                    self.dynaMem.allocatorCalledFor(node.right.name):       #MN: ( ...something... == p )
                    self.dynaMem.setTested(node.right.name)
                elif className(node.right) == "Assignment" and\
                     className(node.right.lvalue) == "ID" and\
                     className(node.right.rvalue) == "FuncCall" and\
                     node.right.rvalue.name.name in allocators:            #MN: ( ...something... == (p=malloc(...)) )
                    self.dynaMem.setTested(node.right.lvalue.name)
        self.generic_visit_exit()

    def visit_UnaryOp(self,node):
        """ The individualized code for traversing a node in
            the AST representing a unary operation.  These
            include increments, decrements, and sizeof.        
        """
        if node == None:
            print 'None passed as node in visit_UnaryOp'
            return
        if node.op == 'sizeof':
            t = node.expr
            while className(t) not in ['ID', 'Typename']:
                t = t.expr
            if className(t) == 'ID' and self.scopeStack.ctype(t.name).isPointer():
                self.warnings.append((node.coord.line,'sizeof applied to pointer'))
        elif node.op in ["++","--","p++","p--"]:
            if self.topName() != 'Assignment':
                  if self.inConditional(node):
                      self.warnings.append((node.coord.line,'Unary op ++ or -- in conditional expression'))
                  if self.topName() == 'BinaryOp':
                      self.warnings.append((node.coord.line,'Unary op ++ or -- part of a larger expression'))
                  if self.topName() == 'ExprList':
                      self.warnings.append((node.coord.line,'Function call with a unary operation argument'))
            elif node.op == '*':
                p = node.expr.name
                if p in self.dynaMem.pointerTarget and self.dynaMem.pointerTarget[p] in self.dynaMem.mallocUntested:
                    self.warnings.append((node.coord.line,'Dereferencing pointer with untested target'))
                if p in self.nullPtrs:
                    self.warnings.append((node.coord.line,'Dereferencing pointer with NULL target'))
            
            self.generic_visit(node)

    def visit_ArrayRef(self,node):
        if node == None:
            print 'None passed as node in visit_ArrarRef'
            return

        s = node.name.name
        print s
        if s in self.dynaMem.pointerTarget and self.dynaMem.pointerTarget[s] in self.dynaMem.mallocUntested:
            self.warnings.append((node.coord.line,'Accessing dynamic array with untested target'))
        self.generic_visit(node)        
        
    def visit_Decl(self,node):
        """ This will record in the scope object the declaration,
            associating the variable name with its type.  These will be
            important to process at this step, because the AST tree does
            not naturally associate IDs to variable types.
        """
	if node == None:
	    print 'None passed as node in visit_Decl'
	    return

        #function declarations
        if className(node.type) in ["FuncDecl"]:
            self.scopeStack.declare(node.name,getVarType(node.type))
            if self.topName() != "FuncDef":     #Function forward declaration
                return                          #No further processing!  All we need is the return type...
        else:
            self.scopeStack.declare(node.name,getVarType(node))
            if self.topName() != "ParamList" and not self.descendantOf('Typedef'):
                if self.scopeStack.ctype(node.name).isPointer(): # How does this handle initialization with a functions call like malloc
                                                                 # also, must handle cast followed by function call
                    if (node.init == None ) and 'extern' not in node.storage: 
                        self.warnings.append((node.coord.line,"Pointer not initialized when declared"))
                    if not self.scopeStack.ctype(node.name).isConst() and node.init != None and className(node.init) == "Constant":
                        if node.init.value not in ['NULL','0']:
                            self.warnings.append((node.init.coord.line,"Pointer initialized to constant value other than NULL"))
                        else: 
                            self.nullPtrs.append(node.name)
            else:
                self.scopeStack.ctype(node.name).makeParameter()
        #self.scopeStack.display()
        self.generic_visit(node)

    def visit_Compound(self,node):
        """ The individualized traversing code for Compound nodes.
            UPDATE FOR C99: Compound nodes now consist of a list
            of child nodes only.
            
            Defines a new scope.
        """
        if node == None:
            print 'None passed as node in visit_Compound'
            return

        self.generic_visit_enter(node)

        #####################################################################################
        # Only enters a new scope if this is *not* a function definition
        #####################################################################################
        if self.topName() not in ["FuncDef"]:
            self.scopeStack.enterScope(node)

        #####################################################################################
        # Need some (major?) work here; now the compound node is just a list of block items #
        #####################################################################################
        #decls deprecated since update to pycparser
        #self.generic_visit_part(node.decls)
        #lineNum = []
        #for d1 in range(len(node.block_items)):
            #if className(node.block_items[d1]) in ["Decl"]:
                #visit_Decl(node.block_items[d1])
                #for d2 in range(d1+1,len(node.block_items)):
                    #visit_Decl(node.block_items[d2])
                    #if className(node.block_items[d2]) in ["Decl"] and\
                        #node.block_items[d1].coord.line == node.block_items[d2].coord.line and\
                            #(self.scopeStack.ctype(node.block_items[d1].name).isPointer() != \
                            #self.scopeStack.ctype(node.block_items[d2].name).isPointer()):
                        #lineNum.append((node.block_items[d1].coord.line,self.scopeStack.ctype(node.block_items[d1].name).base))
        #temp = set(lineNum)
        #for (i,j) in temp:
            #self.warnings.append((i, 'Mixed pointer and non-pointer assignment'))
        #####################################################################################
        # Phew! It appears the mixed pointer/non-pointer declaration detection is working.  #
        # This means that the above lines of commented code should no longer be necessary.  #
        # Let's keep them around for awhile anyway.                                         #
        #####################################################################################
        if node == []:
            self.warnings.append((node.coord.line, 'Empty code block'))
        else:
            # Keep a list of previously encountered declarations for use in identifying
            # mixed pointer/non-pointer declarations in the code
            previousDecls = []
            # Keep a list of line numbers where mixed pointer/non-pointer declarations detected
            lineNum = []
            # Well, we eventually need to iterate through the beast, so here we go...
            # This is the main loop that iterates through the elements in a compound block
            # Should we need an indexing variable?
            for currentItem in node.block_items:
                #debugging info
                #print(className(currentItem))
                #print(previousDecls)
                if className(currentItem) in ["Decl"]:
                    self.visit_Decl(currentItem)
                    for previousDecl in previousDecls:
                        if currentItem.coord.line == previousDecl.coord.line and\
                        (self.scopeStack.ctype(currentItem.name).isPointer() !=
                        self.scopeStack.ctype(previousDecl.name).isPointer()):
                            lineNum.append((currentItem.coord.line,self.scopeStack.ctype(currentItem.name).base))
                    previousDecls.append(currentItem)

            #####################################################################################
            # OK, now we are done iterating through all the (mixed) declarations and statements #
            # in the code block. We now need to take care of the recordkeeping and appending of #
            # appropriate warnings from our processing.                                         #
            #####################################################################################

            # Iterate through the distinct line numbers and report the warnings
            # We do not currently use j, the base type
            for (i,j) in set(lineNum):
                self.warnings.append((i, 'Mixed pointer and non-pointer assignment'))

            # If we aren't in a function definition, then we'll need to exit scope
            if self.topName() not in ["FuncDef"]:
                self.scopeStack.exitScope()
            self.generic_visit_exit()






        #####################################################################################
        # The following is a hot mess. Let me see what I can do to create a newer, better,  #
        # shinier version with good documentation...                                        #
        #####################################################################################

            #i = 0
            #resume = False
            #if self.dynaMem.checkingForMalloc:
                #tempMList1 = []
                #tempMList2 = []
                #warnlist = []
                #leftFromOriginal = []
                #original = list(self.dynaMem.mallocUnwarned) # this creates a copy, not a new reference
                #numOriginal = len(original)
            #while (i <= len(node.stmts)-1):                    Iterate through the statements
                #if self.dynaMem.checkingForMalloc:
                    #self.dynaMem.checkingForMalloc = False
                    #resume = True
                #self.checkStmt(node.stmts[i])                  This just checks to see if it's a useless statement like a constant currently
                #self.visit(node.stmts[i])
                #if resume:
                    #self.dynaMem.checkingForMalloc = True
                #if self.dynaMem.checkingForMalloc:
                    #numOriginal -= 1
                    #leftFromOriginal=[k for k in original if k in self.dynaMem.mallocUnwarned]
                    #tempMList2 = list(tempMList1)
                    #tempMList1 = [k for k in self.dynaMem.mallocUnwarned if k not in original]
                    #warnlist=[item for item in tempMList1 if item in tempMList2]
                    #if warnlist != []:
                        #L = [self.dynaMem.pointersToBlock[p] for p in warnlist][0]
                        #self.warnings.append((node.stmts[i-1].coord.line,
                                              #'Dynamic memory allocator not followed by check for NULL:  variable(s) %s'%L))
                        #for mBlockID in warnlist:
                            #self.dynaMem.warn(mBlockID)
                    #if numOriginal == 0 and leftFromOriginal != []:
                        #L = [self.dynaMem.pointersToBlock[p] for p in leftFromOriginal][0]  # list of list with only one element
            #if className(node.stmts[0]) != 'FuncCall': #Another case?
                            #self.warnings.append((node.stmts[0].coord.line,
                                                  #'Dynamic memory allocator not followed by check for NULL:  variable(s) %s'%L))
            #else:
                            #self.warnings.append((node.stmts[0].name.coord.line,
                                                  #'Dynamic memory allocator not followed by check for NULL:  variable(s) %s'%L))
                        #for l in leftFromOriginal:
                            #self.dynaMem.warn(l)
                #i += 1
            #if self.dynaMem.checkingForMalloc:
                #if tempMList1 + leftFromOriginal != []:
                    #L = [self.dynaMem.pointersToBlock[p] for p in tempMList1+leftFromOriginal][0]
                    #self.warnings.append((node.stmts[-1].coord.line,
                                          #'Dynamic memory allocator not followed by check for NULL:  variable(s) %s: '%L))
                    #for mBlockID in tempMList1+leftFromOriginal:
                        #self.dynaMem.warn(mBlockID)

    def visit_FileAST(self, node):  #Apparently this node is never ever ever ever ever ever visited. Ever.
        """ Defines a new (highest) scope.      
        """
 	if node == None:
	    print 'None passed as node in visit_FileAST'
	    return

        self.scopeStack.enterScope(node)
        self.generic_visit(node)
        self.scopeStack.exitScope()
        
    def visit_FuncDef(self, node):
        """ Defines a new scope
        """
	if node == None:
	    print 'None passed as node in visit_FuncDef'
        return
        self.scopeStack.enterScope(node)
        self.generic_visit(node)
        self.scopeStack.exitScope()

    def visit_FuncDecl(self, node):
        """ This is called upon visiting a function declaration, y'all.
        """

    def visit_FuncCall(self,node):
        """ ...
        """
	if node == None:
	    print 'None passed as node in visit_FuncCall'
	    return

        if className(node.name) == "ID":
            if node.name.name in allocators:
                if className(self.nodeStack[-1]) == "Assignment":
                    if className(self.nodeStack[-1].lvalue) != "ID": # Generates error when lvalue is element of array of pointers! 
                        print "Whoops, big error with assigning an allocator at line %s" %node.coord.line
                    else:
                        self.dynaMem.malloc(self.nodeStack[-1].lvalue.name)
                elif self.topName() == "Decl":
                    self.dynaMem.malloc(self.nodeStack[-1].name)
                else:
                    self.warnings.append((node.name.coord.line,'Return value of dynamic memory allocator not assigned'))
            elif node.name.name == "free":
                ptrName = node.args.exprs[0].name
                if ptrName in self.danglingPtrs:
                    self.warnings.append((node.coord.line,'free called on pointer with previously freed target'))
                retvals = self.dynaMem.free(ptrName)
                if not retvals[0]:
                    if retvals[1] == []:
                        msg = 'Free called on unallocated pointer %s' %ptrName
                    else:
                        msg = 'Call to free results in dangling pointers %s' %(retvals[1])
                        self.danglingPtrs.extend(retvals[1])
                    self.warnings.append((node.name.coord.line,msg)) 
            else:
                pass
        self.generic_visit(node)

    def visit_If(self, node):
        """ The individualized traversing code for If nodes.
            We can check for empty code blocks and such.
        """
	if node == None:
	    print 'None passed as node in visit_If'
	    return

        if node.iftrue == None:
            self.warnings.append((node.coord.line,'Empty if block'))
        if (className(node.iftrue) == 'Compound'):
            if node.iftrue.decls == None and node.iftrue.stmts == None:
                self.warnings.append((node.coord.line,'Empty if block'))
        if node.iffalse!= None:
            if (className(node.iffalse) == 'Compound'):
             	if node.iffalse.decls == None and node.iffalse.stmts == None:
                    self.warnings.append((node.coord.line,'Empty else block'))
        self.generic_visit_enter(node)
        self.generic_visit_part([node.cond],'cond')
        if node.cond != None:
            if className(node.cond) == "Assignment"\
            and className(node.cond.rvalue) == "FuncCall" and node.cond.rvalue.name.name in allocators:
                self.dynaMem.setTested(node.cond.lvalue.name)                                           # if(p=malloc(5)){return 42;}
            elif className(node.cond) == "UnaryOp" and node.cond.op == "!"\
            and className(node.cond.expr) == "Assignment"\
            and className(node.cond.expr.rvalue) == "FuncCall" and node.cond.expr.rvalue.name.name in allocators:
                self.dynaMem.setTested(node.cond.expr.lvalue.name)                                      # if(!(p=malloc(5)) printf("76")
            elif className(node.cond) == "ID":
                self.dynaMem.setTested(node.cond.name)                                                  # if(p) printf("76")
            elif className(node.cond) == "UnaryOp" and node.cond.op == "!"\
            and className(node.cond.expr) == "ID":
                self.dynaMem.setTested(node.cond.expr.name)                                             # if(!p) printf("76")
        self.generic_visit_part([node.iftrue],'iftrue')
        self.generic_visit_part([node.iffalse],'iffalse')
        self.generic_visit_exit

    def visit_While(self, node):
        """ The individualized traversing code for While nodes.
            We can check for empty code blocks, off-by-one errors,
            and such.
        """
	if node == None:
	    print 'None passed as node in visit_While'
	    return

        if node.stmt == None or (node.stmt.decls == None and node.stmt.stmts == None):
            self.warnings.append((node.coord.line,'Empty while block'))
        self.generic_visit(node)
        
    def visit_For(self, node):
        """ The individualized traversing code for For nodes.
            We can check for empty code blocks, off-by-one errors,
            and such.
        """
	if node == None:
	    print 'None passed as node in visit_For'
	    return
        if node.stmt == None or (className(node.stmt) == 'Compound' and node.stmt.decls == None and node.stmt.stmts == None):
            self.warnings.append((node.coord.line,'Empty for block'))
        if node.init != None and node.cond != None and node.init.__class__.__name__ == "Assignment" and node.cond.__class__.__name__ == "BinaryOp":
            if node.init.rvalue.__class__.__name__ == "Constant" and node.init.rvalue.value == "0" and (node.cond.op == "<=" or node.cond.op == ">="):
                self.warnings.append((node.coord.line,'Possible off-by-one error in loop'))
            if node.init.rvalue.__class__.__name__ == "Constant" and node.init.rvalue.value == "1" and (node.cond.op == "<" or node.cond.op == ">"):
                self.warnings.append((node.coord.line,'Possible off-by-one error in loop'))
        self.generic_visit(node)

    def visit_Switch(self, node): # This code assumes that ; has been inserted after each case declaration using fixCase.py
        """ The custom traversing code for a Switch node.
            We can check for missing or inappropriate breaks or conditions.
        """
	if node == None:
	    print 'None passed as node in visit_Switch'
	    return

        if node.stmt == None or (node.stmt.decls == None and node.stmt.stmts == None):
            self.warnings.append((node.coord.line,'Empty switch statement block'))
        elif node.stmt.__class__.__name__ != "Compound":
            self.warnings.append((node.coord.line,'Single case statement in switch'))
            return
        else: # At this point, node.stmt is a Compound node
            stmtCount = len(node.stmt.stmts)
            caseIndices = []
            for i in range(stmtCount):
                if className(node.stmt.stmts[i]) in ['Case','Default']:
                    caseIndices.append(i)
            caseCount = len(caseIndices)
            for k in range(caseCount):
                stopIndex = stmtCount if k == caseCount-1 else caseIndices[k+1]
                breakFound = False
                for j in range(caseIndices[k]+1,stopIndex):
                    if className(node.stmt.stmts[j]) == 'Break':
                        breakFound = True
                        if j != stopIndex-1:
                            self.warnings.append((node.stmt.stmts[j].coord.line,
                                                  'Break statement in the middle of a case code block'))
                if k < caseCount-1 and caseIndices[k+1] != caseIndices[k] + 1 and  not breakFound:
                    print k, 
                    self.warnings.append((node.stmt.stmts[stopIndex-1].coord.line,
                                          'Case/Default block of switch statement not terminated by a break'))

        self.generic_visit(node)
        
    def visit_Case(self, node):
        """ The custom code for traversing a Case node.
            Most of the checks for interesting runtime errors occur in
            the visit_Switch method
        """
	if node == None:
	    print 'None passed as node in visit_Case'
	    return

        self.generic_visit(node)



        
if __name__ == "__main__":
    if len(sys.argv) == 2:
        filename = sys.argv[1]
        print 'Processing %s' %filename
        ast,numlines = getAST(filename)
        # ast.show(showcoord=True)
        S = getWarnings(filename)
        print(S)
    else:
        print 'Arguments incorrect: should consist of the filename'
