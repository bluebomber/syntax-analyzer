#!/usr/bin/python

from pycparser import c_parser, c_ast, parse_file
from clueUtils import *

import sys, math, os, sys, os

tutorial_dir = '/home/rtindell/clue/Tutorials' 
base_path = tutorial_dir+os.sep+'utils'
fakes_path = '%s%sfake_libc_include' %(base_path,os.sep)

#FUTURE: extend malloc to allocators
tester_ops = ['If','While','DoWhile','For']

#Alias for an empty set
empty_set = set([])

# Portable cpp path for Windows and Linux/Unix
CPPPATH = 'cpp'

def getAST(filename): #basename = appdir\\Tutorials\\utils
    ast = None
    ast = parse_file(filename, use_cpp=True,
            cpp_path=CPPPATH, 
            #cpp_args='-I'+fakes_path)
            #cpp_args='-I/clue/Tutorials/utils/fake_libc_include')
            cpp_args='-Ifake_libc_include')
    myFile = open(filename)
    numlines = len(myFile.readlines())
    myFile.close()
    #ast.show()
    return ast, numlines

def printWarnings(filename):
    ast, numlines = getAST(filename)
    myFile = open(filename)
    #Pass one: Get allocators (skipping main for now (should I not?))
    a = allocatorVisitor()
    # This visit method updates the
    #   checkedAllocators & uncheckedAllocators
    #   list class variables within class dynamicMemory
    # This first pass produces no warnings
    a.visit(ast)

    #print("Checked: {"+", ".join(dynamicMemory.checkedAllocators)+"}")
    #print("Unchecked: {"+", ".join(dynamicMemory.uncheckedAllocators)+"}")
    
    # Pass two: Visit
    # This second pass produces warning messages
    v = smatchVisitor()
    v.visit(ast)
    myFile.close()
    print("\n")
    v.displayWarnings(numlines)

#TODO: we have two getWarnings functions: this one (global in the module), and the method of the smatchVisitor class
def getWarnings(filename):
    ast, numlines = getAST(filename)
    myFile = open(filename)
    #Pass one: Get allocators (skipping main for now (should I not?))
    a = allocatorVisitor()
    # This visit method updates the
    #   checkedAllocators & uncheckedAllocators
    #   list class variables within class dynamicMemory
    # This first pass produces no warnings
    a.visit(ast)

    #print("Checked: {"+", ".join(dynamicMemory.checkedAllocators)+"}")
    #print("Unchecked: {"+", ".join(dynamicMemory.uncheckedAllocators)+"}")
    
    # Pass two: Visit
    # This second pass produces warning messages
    s = smatchVisitor()
    s.visit(ast)
    myFile.close()
    return s.getWarnings(numlines)

def className(node=None):
    if node is None:
        return None
    else:
        return node.__class__.__name__

def getCType(node):
    """
        This function returns a cType object representing the C type
        of the Decl which node represents.
    """
    tempType = cType()
    if className(node) == 'Decl':
        tempType.name = node.name
        traverseType = node.type
        while (True):
            if className(traverseType) == 'PtrDecl':
                tempType.typeList += [('*',traverseType.quals)]
                traverseType = traverseType.type
            elif className(traverseType) == 'ArrayDecl':
                tempType.typeList += [('array',[])]
                traverseType = traverseType.type
            elif className(traverseType) == 'TypeDecl':
                #tempType.typeList += [('type: '+traverseType.declname,traverseType.quals)]
                traverseType = traverseType.type
            elif className(traverseType) == 'FuncDecl':
                tempType.typeList +=('func',[])
                break
            elif className(traverseType) == 'IdentifierType':
                tempType.typeList += [(''.join(traverseType.names),[])]
                break
            elif className(traverseType) == 'Struct':
                tempType.typeList += [('struct '+traverseType.name,[])]
                break
            else:
                print("Error extracting C type from node "+className(traverseType)+"! Quitting.")
                break
    return tempType

#TODO: Make this more robust. right now it's more-or-less ad-hoc.
class cType():
    """
        Class for representing types in C.
        The internal type is:
          string * (string * string list) list
        Objects of this class have two members:
        name: The variable name of the object, or None.
        typeList: A list of tuples. The entire list represents
                  the C type of a variable, including at each
                  stage the type modifiers.
        
        Wishlist for the future: Extend this representation to
        support recursive types like functions, etc.
        
        For example, the following:

          const int * mypointer;

        Would be represented internally by:

          name = 'mypointer'
          typeList = [('int',['const']),('*',[])]
    """
    def __init__(self, type=None, name=None):
        self.name = name
        self.typeList = [type] if type != None else []
        
    def isPointer(self):
        return self.typeList[0][0] == '*'
            
    def isType(self, type):
        return self.typeList[0][0] == type
            
    def isConst(self):
        return 'const' in reduce ((lambda x,y: x+y), [t[1] for t in self.typeList])

    def isExtern(self):
        return 'extern' in reduce ((lambda x,y: x+y), [t[1] for t in self.typeList])
            
    def makeParameter(self):
        self.typeList[0][1].append('param')
        
    def isParameter(self):
        return 'param' in reduce ((lambda x,y: x+y), [t[1] for t in self.typeList])

    def getName(self):
        return self.name

    def display(self):
        printString = self.name + " : "
        for typePart in self.typeList:
            printString += "("+", ".join(typePart[1])+typePart[0]+")"
        print(printString)
            
def getPointerID(node):
    """
        This function returns the ID (qualified variable name) of a variable. This is
        intended and currently used for assignment of a return value of an allocator
        to a pointer variable.

        *head = makeNewListNode()

        Would return '*head'
    """
    if className(node) == "UnaryOp":
        return node.op + getPointerID(node.expr)
    elif className(node) == "ID":
        return node.name
    elif className(node) == "StructRef":
        return getPointerID(node.name) + node.type + getPointerID(node.field)
    else:
        return "UNKNOWN-ID"
                
            
class variableScope():
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
        self.scope = [{}]
        self.scopeNode = [None]

    def enterScope(self, node):
        self.scope.append(dict(self.scope[-1]))
        self.scopeNode.append(node)

    def exitScope(self):
        self.scope.pop()
        self.scopeNode.pop()
        
    def declare(self, variableID, cType):
        self.scope[-1][variableID] = cType

    #def ctype(self, ID):
    def getVariableType(self, variableID):
        if variableID in self.scope[-1]:
            return (self.scope[-1])[variableID]
        else:
            print "Error!  Variable requested (%s) not found in current scope!" %variableID
            
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

class warning():
    """
        This is a warning object. Each warning object will have
        at least a line number, an identifier  and a string. Warnings may
        also take arguments, for instance, the warning may want
        to refer to a line number.
    """
    warning_list = [
                    (0,"assignment of non-initialized pointer"),
                    (1,"pointer assignment causes memory leak"),
                    (2,"possible use of = instead of == in condition"),
                    (3,"assignment to parameter in function body"),
                    (4,"possible use of & instead of && in function body"),
                    (5,"possible use of | instead of || in function body"),
                    (6,"sizeof applied to pointer"),
                    (7,"unary op ++ or -- in conditional expression"),
                    (8,"unary op ++ or -- part of a larger expression"),
                    (9,"function call with a unary operation argument"),
                    (10,"dereferencing pointer with untested target"),
                    (11,"dereferencing pointer with NULL target"),
                    (12,"accessing dynamic array with untested target"),
                    (13,"pointer initialized to constant value other than NULL"),
                    (14,"empty code block"),
                    (15,"block allocated on line %s not tested for successful allocation within %s statements"), #note that this error requires two extra string arguments
                    (16,"mixed pointer and non-pointer declaration"),
                    (17,"potential memory leak: memory block allocated at line %s has not been freed"),
                    (18,"function with non-VOID return type missing a return statement"),
                    (19,"return value of dynamic memory allocation not stored"),
                    (20,"free() called on pointer with previously freed target. target previously freed at line %s"),
                    (21,"empty if block"),
                    (22,"empty else block"),
                    (23,"empty while block"),
                    (24,"empty for block"),
                    (25,"possibly off-by-one error in loop"),
                    (26,"empty switch statement block"),
                    (27,"single case statement in switch statement"),
                    (28,"break statement in the middle of a case code block"),
                    (29,"case block or default block of switch statement not terminated by a break"),
                   ]
        warning_list_ids = [w.get_id() for w in warning_list]

    def __init__(self, line_number, warning_id, args = ()):
        self.warning_id = warning_id
        self.args_passed = tuple(args)
        self.num_args = error_string.count("%s")
        self.line_number = line_number
        if warning_id not in warning.warning_list_ids:
            raise Exception("tried to create a warning whose ID does not exist in the list")
        if self.num_args != len(args):
            raise Exception("tried to create warning %s, but %s/%s arguments were passed to it."%(self.warning_id,len(args),self.num_args))
        self.warning_message = reduce(lambda a, v: v[1] if v[0] == self.warning_id else a, warning.warning_list, "")

    def __str__(self):
        return self.toString()

    def toString(self):
        return self.warning_message % self.args_passed

    def getFullMessage(self):
        return "line "+str(self.line_number)+": "+self.toString()

    def getID(self):
        return self.warning_id

    def printWarning(self, args):
        print(self.toString)

    def printFullMessage:
        print("line "+str(self.line_number)+": "+self.toString())


class warningManager():
    """
        This encapsulates the functionality we require to record,
        manipulate, organize, and print the common runtime errors
        we encounter in the students' code. The instance keeps a
        list of (line number, warning string) pairs.
    """

    def __init__(self):
        self.warning_list = []
        
    def addWarning(self, warning_id, args = None):
        self.warning_list

    def sort(self, key='line'):
        if key == 'line':
            #self.list = sorted(self.list, key=lambda warning: warning[0])
            self.warning_list.sort(key=lambda warning: warning.)
        elif key == 'error':
            #self.list = sorted(self.list, key=lambda warning: warning[1])
            self.warning_list.sort(key=lambda warning: str(warning))
        else:
            raise Exception("no way for me to sort all these many common mistakes!")
            
    #def display(self, numPadding = 100):
        #retString = ''
        #printStr = "%" + str(int(math.log10(numPadding))+2) + "s:  %" + "s\n"
        #self.list.sort()
        #for i in self.list:
            #retString += printStr % (i[0], i[1])
        #print(retString)

    def getFullWarnings(self):
        self.sort()
        retString = ''
        #printStr = "%" + str(int(math.log10(numPadding))+2) + "s:  %" + "s\n"
        #self.list.sort()
        for warning in self.warning_list:
            retString += "\n"
        return retString

    def getlist(self, numPadding = 100):
        retString = ''
        printStr = "%" + str(int(math.log10(numPadding))+2) + "s:  %" + "s\n"
        self.list.sort()
        L = []
        for i in self.list:
            L.append(printStr % (i[0], i[1]))
        return L

class memoryBlock():
    """ memoryBlock objects each represent a dynamically allocated block of memory,
        and they store the following information about their block:
        
        blockID:
            ID of this block, i.e. its index

        pointers:
            set of IDs of pointers that point to this block.

        timer:
            the number of statements left to process after this block's
            allocation before an unchecked allocation warning is issued.
            This is initialized to dynamicMemory.checkthreshold.

        lineChecked:
            The line number where a pointer to this block was compared
            against NULL, '\0', zero, false, etc. This will be negative if such a
            check has not yet occurred.

        lineAllocated:
            The line number where the allocation occurred.

        lineFreed:
            The line number where a free occurred. This will be negative if the block
            has not been freed yet.

        removePointer:
            Removes a pointer from the set of pointers pointing at this block

        danglingPointers:
            A list of pointers to this block. This returns None of the block has not yet
            been freed, otherwise it returns the list of pointers still pointing to it.
            
        NOTE: For lineChecked/Freed/Assigned, -1 signifies that the respective action has
              not occurred, and a positive value indicates it has happened, but it may not
              have happened explicitly in the code, but rather could have been set as a flag
              in order to prevent warnings.
    """ 

    def __init__(self, blockID, checkThreshold, lineAllocated, lineChecked=-1):
        self.blockID = blockID
        self.pointers = empty_set.copy()
        self.lineChecked = lineChecked
        self.lineFreed = -1
        self.lineAllocated = lineAllocated
        self.timer = checkThreshold

    # Has the allocation been checked?
    def checked(self):
        return self.lineChecked >= 0

    # Has the memory been freed?
    def freed(self):
        return self.lineFreed >= 0

    # Called when comparison of pointer to memory block detected
    def check(self, line):
        self.lineChecked = line
        self.timer = -1

    # Called when free() called on pointer to memory block
    def free(self, line):
        self.lineFreed = line

    # dynamicMemory.tick() calls this on each block in its record after
    # each statement in a compound node.
    def decrement(self):
        self.timer -= 1

    def addPointer(self, pointerID):
        # FYI: add() is a method defined for sets
        self.pointers.add(pointerID)

    def removePointer(self, pointerID):
        if pointerID in self.pointers:
            self.pointers.remove(pointerID)
        else:
            print("Error! I tried to remove a pointer from a memory block, but it didn't work!")


class dynamicMemory():
    """
        An instance of this class will be a list of memoryBlock objects, a dictionary
        for looking up a block ID based on pointer ID, together with access methods.

        NOTE: This class has class variables uncheckedAllocators and checkedAllocators, both lists
        of functionIDs, and the first pass on the code, executed by allocatorVisitor, updates these
        lists appropriately. This class also contains the class variable checkThreshold, a whole
        number representing how many lines may pass after an unchecked allocation occurs before
        the program must check the allocation.
    """

    uncheckedAllocators = ['malloc','calloc','strdup']
    checkedAllocators = []

    #This is the number of statements (at the same scope level) after
    # an allocation occurs before a warning is issued. Set equal to 1
    # to require code to check malloc occur immediately at the next
    # statement.
    checkThreshold = 1

    def __init__(self):
        self.blocks = [memoryBlock(blockID=0, checkThreshold=-1, lineAllocated=-1, lineChecked=0)]
        self.pointerTarget = {}
        self.nextBlockID = 1
        self.initializedPointers = empty_set.copy()

    def allocate(self, line):
        self.blocks.append(memoryBlock(self.nextBlockID, dynamicMemory.checkThreshold, line))
        self.nextBlockID += 1

    # Check a block of memory either by blockid or pointer name
    def check(self, line, pointerID = None, blockID = None):
        if (pointerID == None and blockID == None or pointerID != None and blockID != None):
            print("Error! You must provide exactly one of either a pointerID or a blockID to check!")
            return None
        if pointerID != None:
            #print("Checking off on line "+str(line)+": "+pointerID)
            # For each block in list of all dynamically allocated memory blocks...
            # Mark the block as checked if the provided pointer is pointing to this block.
            if self.pointsAtMemoryBlock(pointerID):
                self.pointerTarget[pointerID].lineChecked = line
                self.pointerTarget[pointerID].timer = -1
        else:
            self.blocks[blockID].lineChecked = line
            self.blocks[blockID].timer = -1

    # Free a block of memory identified either by blockID or a pointer name
    def free(self, line, pointerID = None, blockID = None):
        if (pointerID == None and blockID == None or pointerID != None and blockID != None):
            print("Error! You must provide exactly one of either a pointerID or a blockID to free!")
            return None
        if pointerID != None:
            # For each block in list of all dynamically allocated memory blocks...
            if self.pointsAtMemoryBlock(pointerID):
                self.pointerTarget[pointerID].lineFreed = line
        else:
            self.blocks[blockID].lineFreed = line

    def initialize(self, pointerID):
        self.initializedPointers.add(pointerID)

    def initialized(self, pointerID):
        return pointerID in self.initializedPointers

    # Important note: This is for assigning pointer IDs to block IDs, *not* for
    #   copying pointer to pointer! That must be done via the copyPointer method.
    def linkPointerToBlock(self, pointerID, blockID):
        self.blocks[blockID].addPointer(pointerID)
        self.pointerTarget[pointerID] = self.blocks[blockID]

    def nullify(self, pointerID):
        self.linkPointerToBlock(pointerID, 0)

    # This is for the c-like statement
    #  void * a, * b;
    #  a = b;
    # That is, this only updates pointerIDA.
    # Underneath the hood, like nullify(), this is an alias for
    # calls to linkPointerToBlock().
    def copyPointer(self, line, pointerIDA, pointerIDB):
        self.erasePointer(pointerIDA)
        if self.pointsAtMemoryBlock(pointerIDB):
            self.linkPointerToBlock(pointerIDA, self.pointerTarget[pointerIDB])

    # This function removes a pointer from the structure, erasing the fact it ever existed
    def erasePointer(self, pointerID):
        if self.pointsAtMemoryBlock(pointerID):
            self.pointerTarget[pointerID].pointers.remove(pointerID)
            del self.pointerTarget[pointerID]

    # This is simply for allocation and assignment in a single call
    # Logically equivalent to linkPointerToBlock(pointerID, allocate())
    def initializePointer(self, line, pointerID, checked=False):
        self.allocate(line)
        self.linkPointerToBlock(pointerID,self.nextBlockID-1)
        if checked:
            self.check(line, blockID = self.nextBlockID-1)

    # This returns true of there is an unfreed block without any pointers pointing at it
    def isMemoryLeak(self, pointerID):
        return reduce ((lambda block, rest: (block.pointers == empty_set and not block.freed()) or rest), self.blocks)

    # True if pointerID points to some actual (non NULL) memory block
    def pointsAtMemoryBlock(self, pointerID):
        return pointerID in self.pointerTarget and not self.pointerTarget[pointerID] == 0

    # This constructs and returns a list of pointers IDs of dangling pointers
    def danglingPointers(self):
        blockList = [block for block in self.blocks if block.freed()]
        returnList = []
        for block in blockList:
            returnList.extend(block.pointers)
        return returnList

    # This returns a list of pointers pointing to NULL (the 0 block)
    def nullPointers(self):
        return self.blocks[0].pointers

    def tick(self, line):
        blocklist = [block for block in self.blocks if not block.checked()]
        for block in blocklist:
            if block.timer == 0:
                block.check(line)
            elif block.timer > 0:
                block.decrement()

    def unfreedBlocks(self):
        return [block for block in self.blocks[1:] if not block.freed()]

    def expiredBlocks(self):
        return [block for block in self.blocks[1:] if block.timer == 0]

    def purge(self):
        self.__init__()

    def display(self, info):
        #info must be an informative string telling where the state of dynamic memory is being polled
        msg = "-----------------------------------------------------------------------------------\n"
        msg = msg + "|                              Dynamic Memory State\n"
        msg = msg + "|                              "+str(info)+"\n"
        msg = msg + "-----------------------------------------------------------------------------------\n"
        msg = msg + "# dynamic memory blocks:        "+str(len(self.blocks))+"\n"
        msg = msg + "bid\t\tla\t\tlc\t\tlf\t\tpointers at it\t\t\ttimer"
        print(msg)
        for block in self.blocks:
            #print("block #:"+str(block.blockID)+", pointers: "+str(block.pointers))
            pointerlist = "{" + ", ".join(list(block.pointers)) + "}"
            msg = str(block.blockID)+"\t\t"
            msg += str(block.lineAllocated)+"\t\t"
            msg += str(block.lineChecked)+"\t\t"
            msg += str(block.lineFreed)+"\t\t"
            msg += pointerlist+"\t\t\t\t"
            msg += str(block.timer)
            print(msg)
        print("pointerTarget status:")
        print(", ".join([pointerID+"->"+str(self.pointerTarget[pointerID].blockID) for pointerID in self.pointerTarget]))
        print("initialized pointer status:")
        print(", ".join(self.initializedPointers))
        print("\n\n")


class allocatorVisitor(c_ast.NodeVisitor):
    """
        The object of this class traverses the nodes of the AST and finds all the
        functions who return a pointer to dynamically allocated memory.

        This is the object that makes the first traversal/pass on the AST.
    """
    def __init__(self):
        self.nodeStack = [] # Note that the stack does NOT contain the current node, just its ancestors
        self.scopeStack = variableScope()
        self.dynaMem = dynamicMemory()
        self.currentFunction = None # This points to the name of the current function def being traversed.

    def parentName(self):
        top = self.nodeStack[-1]
        if top != None:
            return className(top)
        else:
            return 'None'

    def inConditional(self,node):
        for i in range(len(self.nodeStack)):
            if className(self.nodeStack[i]) in tester_ops:
                if node == self.nodeStack[i].cond:
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

    def generic_visit(self, node):
        """ Called if no explicit visitor function exists for a 
            node. Implements preorder visiting of the node.
        """
        #print"visiting "+className(node)
        if node is not None:
            self.nodeStack.append(node)
            if 'children' in dir(node):
                for (childname, child) in node.children():
                    self.visit(child)
            self.nodeStack.pop()

    def visit_Assignment(self,node):
        if node is None:
            print 'None passed as node in visit_Assignment'
            return

        if node.op == '=':
            if className(node.lvalue) == 'ID' and self.dynaMem.pointsAtMemoryBlock(node.lvalue.name)\
            and className(node.rvalue) == 'ID' and  self.dynaMem.pointsAtMemoryBlock(node.rvalue.name):
                self.dynaMem.copyPointer(node.coord.line, node.lvalue.name, node.rvalue.name)
        else:
            print("Error processing this assignment node... What other kind of operator can an assignment have besides '='?!")
        self.generic_visit(node)
                
    def visit_BinaryOp(self,node):
        if node.op in [ '==', '!=', '>', '<','<=','>=' ]:
            if (className(node.right) == "ID" and\
                node.right.name in ["NULL",'0']) or\
                (className(node.right) == "Constant" and\
                node.right.value == '0'):
                # If the left operand is a pointer pointing to an allocated block of memory, mark that pointer/block as tested
                #MN: ( p == NULL ) or ( p == 0 )
                #print(str(self.dynaMem.pointsAtMemoryBlock(node.left.name)))
                if className(node.left) == "ID" and self.dynaMem.pointsAtMemoryBlock(node.left.name):
                    self.dynaMem.check(node.coord.line, node.left.name)
                # The following catches some forms of immediate comparison after an allocation
                # ((p=malloc(...)) == NULL) or ((p=malloc(...)) == 0 )
                elif className(node.left) == "Assignment" and\
                     className(node.left.lvalue) == "ID" and\
                     className(node.left.rvalue) == "FuncCall" and\
                     node.left.rvalue.name.name in dynamicMemory.uncheckedAllocators:
                    self.dynaMem.check(node.coord.line, node.left.lvalue.name)
            # If comparing against any of the many flavors of NULL, this time NULL on the left...
            elif (className(node.left) == "ID" and\
                 node.left.name in ["NULL", '0']) or\
                 (className(node.left) == "Constant" and\
                    node.left.value == '0'):                                
                if className(node.right) == "ID" and\
                   self.dynaMem.pointsAtMemoryBlock(node.right.name):
                    self.dynaMem.check(node.coord.line, node.right.name)                 #MN: ( NULL/0 == p )
            else: # ADDED BY RT 7/25/2010
                if  className(node.right) == "ID" and\
                    self.dynaMem.pointsAtMemoryBlock(node.right.name):       #MN: ( ...something... == p )
                    self.dynaMem.check(node.coord.line, node.right.name)
                elif className(node.right) == "Assignment" and\
                     className(node.right.lvalue) == "ID" and\
                     className(node.right.rvalue) == "FuncCall" and\
                     node.right.rvalue.name.name in dynamicMemory.uncheckedAlllocators:            #MN: ( ...something... == (p=malloc(...)) )
                    self.dynaMem.check(node.coord.line, node.right.lvalue.name)
        self.generic_visit(node)

    def visit_Compound(self,node):
        if node == None:
            print 'None passed as node in visit_Compound'
            return
        self.scopeStack.enterScope(node)
        self.nodeStack.append(node)
        self.generic_visit(node)
        self.scopeStack.exitScope()
        self.nodeStack.pop()

    def visit_FileAST(self, node): #Vital assumption: This node is only visited once during any execution
        """ Defines a new (highest) scope.      
        """
        if node is None:
            print 'None passed as node in visit_FileAST'
            return
        # it will traverse as normal, but skipping the main function at first
        self.scopeStack.enterScope(node)
        self.nodeStack.append(node)
        self.generic_visit(node)
        self.nodeStack.pop()
        self.scopeStack.exitScope()
        
    def visit_FuncDef(self, node):
        self.scopeStack.enterScope(node)
        oldfunction = self.currentFunction
        self.currentFunction = node.decl.name
        self.generic_visit(node)
        self.dynaMem.__init__()
        self.currentFunction = oldfunction
        self.scopeStack.exitScope()

    def visit_FuncCall(self, node):
        if className(node.name) == "ID":
            if node.name.name in dynamicMemory.uncheckedAllocators:
                if self.parentName() == "Assignment":
                    self.dynaMem.initializePointer(node.coord.line, getPointerID(self.nodeStack[-1].lvalue), False)
                elif self.parentName() == "Decl":
                    self.dynaMem.initializePointer(node.coord.line, self.nodeStack[-1].name)
            elif node.name.name in dynamicMemory.checkedAllocators:
                if self.parentName() == "Assignment":
                    self.dynaMem.initializePointer(node.coord.line, getPointerID(self.nodeStack[-1].lvalue), True)
            elif node.name.name == "free":
                ptrName = node.args.exprs[0].name
        self.generic_visit(node)

    def visit_If(self, node):
        """ The individualized traversing code for If nodes.
            We can check for empty code blocks and such.
        """
        if node == None:
            print 'None passed as node in visit_If'
            return

        if node.cond != None:
            if className(node.cond) == "Assignment"\
            and className(node.cond.rvalue) == "FuncCall" and node.cond.rvalue.name.name in dynamicMemory.uncheckedAllocators:
                self.dynaMem.check(node.coord.line, node.cond.lvalue.name)                                           # if(p=malloc(5)){return 42;}
            elif className(node.cond) == "UnaryOp" and node.cond.op == "!"\
            and className(node.cond.expr) == "Assignment"\
            and className(node.cond.expr.rvalue) == "FuncCall" and node.cond.expr.rvalue.name.name in dynamicMemory.uncheckedAllocators:
                self.dynaMem.check(node.coord.line, node.cond.lvalue.name)                                           # if(p=malloc(5)){return 42;}
            elif className(node.cond) == "ID":
                self.dynaMem.check(node.coord.line, node.cond.name)   #if(p) printf("foo")
            elif className(node.cond) == "UnaryOp" and node.cond.op == "!"\
            and className(node.cond.expr) == "ID":
                self.dynaMem.check(node.coord.line, node.cond.name)                                             # if(!p) printf("76")
        self.generic_visit(node)

    def visit_Return(self, node):
        """ The custom code for traversing a return statement.
            This is where we should be processing and updating
            the allocators[] list!
        """
        if className(node.expr) == "ID":
            if self.dynaMem.pointsAtMemoryBlock(node.expr.name):
                if not self.dynaMem.pointerTarget[node.expr.name].checked():
                    dynamicMemory.uncheckedAllocators.append(self.currentFunction)
                else:
                    dynamicMemory.checkedAllocators.append(self.currentFunction)


class smatchVisitor(c_ast.NodeVisitor):
    """
        The object of this class traverses the nodes of the AST and issues warnings.
        
        This object performs the second traversal/pass on the AST, after the allocatorVisitor.
    """

    def __init__(self):
        self.warnings = warningManager() # BIZARRE - apparently if we don't pass in [], list from previous call retained!
        self.nodeStack = [] # Note that the stack does NOT contain the current node, just its ancestors
        self.scopeStack = variableScope()
        self.dynaMem = dynamicMemory()
        self.branchTaken = []   # This is a stack that corresponds to the name of the childnode pointer traversed;
                                # A stack that corresponds to nodestack.
                                # IE branchTaken[i] gives the name of the childnode instance variable the visitor took
                                # ...leaving node self.nodeStack[i] to arrive at node self.nodeStack[i+1]
                                # If it is only one such node in a list of nodes, it returns the name of the list
        self.currentFunction = None # This points to the FuncDef node currently being traversed.
        self.returnEncountered = True # Used in visit_FuncDef to determine if a return expression was encountered

    def parentName(self):
        top = self.nodeStack[-1]
        if top != None:
            return className(top)
        else:
            return 'None'

    def inConditional(self,node):
        for i in range(len(self.nodeStack)):
            if className(self.nodeStack[i]) in tester_ops:
                if node == self.nodeStack[i].cond:
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
            
    def displayWarnings(self, buff=None):
        """ This method simply calls the warnings
            class's display method.        
        """
        return self.warnings.display(buff)  # return self.

    def getWarnings(self, buff=None):
        """ This method simply calls the warnings
            class's getlist method.        
        """
        return self.warnings.getlist(buff)  # return self.

    def generic_visit(self, node):
        """ Called if no explicit visitor function exists for a 
            node. Implements preorder visiting of the node.
        """
        #print"visiting "+className(node)
        if node is not None:
            self.nodeStack.append(node)
            # the children method now returns an iterable of (childname, childnode) pairs
            for (childname, child) in node.children():
                self.visit(child)
            self.nodeStack.pop()

    def visit_Assignment(self,node):
        """ This is what a visitor node executes when it reaches
            an assignment node in the tree.        
        """
        if className(node.rvalue) == 'ID':
            if self.scopeStack.getVariableType(node.rvalue.name).isPointer():
                if not self.dynaMem.initialized(node.rvalue.name):
                    self.warnings.append((node.coord.line,'Assignment of non-initialized pointer.'))
                else:
                    # If the lvalue is also a pointerID, it is now initialized
                    if className(nod.lvalue) == 'ID':
                        self.dynaMem.initialize(node.lvalue.name)
                if self.dynaMem.pointsAtMemoryBlock(node.lvalue.name):
                    # warn about memory leak
                    if len(self.dynaMem.pointerTarget[node.lvalue.name].pointers) == 1:
                        self.warnings.append((node.coord.line, "Pointer assignment causes memory leak."))
                    self.dynaMem.copyPointer(node.coord.line, node.lvalue.name, node.rvalue.name)
        if self.inConditional(node) and className(node.rvalue) != "FuncCall":
            self.warnings.append((node.coord.line,'Possible use of = for == in condition'))
        if className(node.lvalue) == 'ID':
            if self.scopeStack.getVariableType(node.lvalue.name).isParameter():
                self.warnings.append((node.coord.line,'Assignment to parameter in function body'))
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
        #self.nodeStack.append(node)
        self.generic_visit(node)
        #self.visit(node.right)
        if node.op in ['&','|']:
            if self.inConditional(node) and not self.parentName() == 'Assignment':  
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
                if className(node.left) == "ID" and self.dynaMem.pointsAtMemoryBlock(node.left.name):
                    self.dynaMem.check(node.coord.line, node.left.name)
                # The following catches some forms of immediate comparison after an allocation
                # ((p=malloc(...)) == NULL) or ((p=malloc(...)) == 0 )
                elif className(node.left) == "Assignment" and\
                     className(node.left.lvalue) == "ID" and\
                     className(node.left.rvalue) == "FuncCall" and\
                     node.left.rvalue.name.name in dynamicMemory.uncheckedAllocators:
                    self.dynaMem.check(node.coord.line, node.left.lvalue.name)
            # If comparing against any of the many flavors of NULL, this time NULL on the left...
            elif (className(node.left) == "ID" and\
                 node.left.name in ["NULL", '0']) or\
                 (className(node.left) == "Constant" and\
                    node.left.value == '0'):                                
                if className(node.right) == "ID" and\
                   self.dynaMem.pointsAtMemoryBlock(node.right.name):
                    self.dynaMem.check(node.coord.line, node.right.name)                 #MN: ( NULL/0 == p )
            else: # ADDED BY RT 7/25/2010
                if  className(node.right) == "ID" and\
                    self.dynaMem.pointsAtMemoryBlock(node.right.name):       #MN: ( ...something... == p )
                    self.dynaMem.check(node.coord.line, node.right.name)
                elif className(node.right) == "Assignment" and\
                     className(node.right.lvalue) == "ID" and\
                     className(node.right.rvalue) == "FuncCall" and\
                     node.right.rvalue.name.name in dynamicMemory.uncheckedAllocators:            #MN: ( ...something... == (p=malloc(...)) )
                    self.dynaMem.check(node.coord.line, node.right.lvalue.name)

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
            if className(t) == 'ID' and self.scopeStack.getVariableType(t.name).isPointer():
                self.warnings.append((node.coord.line,'sizeof applied to pointer'))
        elif node.op in ["++","--","p++","p--"]:
            if self.parentName() != 'Assignment':
                  if self.inConditional(node):
                      self.warnings.append((node.coord.line,'Unary op ++ or -- in conditional expression'))
                  if self.parentName() == 'BinaryOp':
                      self.warnings.append((node.coord.line,'Unary op ++ or -- part of a larger expression'))
                  if self.parentName() == 'ExprList':
                      self.warnings.append((node.coord.line,'Function call with a unary operation argument'))
        elif node.op == '*':
            p = node.expr.name
            if p in self.dynaMem.pointerTarget and not self.dynaMem.pointerTarget[p].checked():
                self.warnings.append((node.coord.line,'Dereferencing pointer with untested target'))
            if p in self.dynaMem.nullPointers():
                self.warnings.append((node.coord.line,'Dereferencing pointer with NULL target'))
        self.generic_visit(node)

    def visit_ArrayRef(self,node):
        if node == None:
            print 'None passed as node in visit_ArrarRef'
            return

        s = node.name.name
        if s in self.dynaMem.pointerTarget and not self.dynaMem.pointerTarget[s].checked():
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
        if className(node.type) in ["FuncDecl"]:
            self.scopeStack.declare(node.name,getCType(node.type))
            if self.parentName() != "FuncDef":     #Function forward declaration
                return                          #No further processing!  All we need is the return type...
        else:
            self.scopeStack.declare(node.name,getCType(node))
            if self.parentName() != "ParamList" and not self.descendantOf('Typedef'):
                if self.scopeStack.getVariableType(node.name).isPointer():
                    if not self.scopeStack.getVariableType(node.name).isConst() and node.init != None and className(node.init) == "Constant":
                        if node.init.value not in ['NULL','0']:
                            self.warnings.append((node.init.coord.line,"Pointer initialized to constant value other than NULL"))
                        else: 
                            self.dynaMem.nullify(node.name)
            else:
                self.scopeStack.getVariableType(node.name).makeParameter()
        self.generic_visit(node)

    def visit_Compound(self,node):
        """ The individualized traversing code for Compound nodes.
            UPDATE FOR C99: Compound nodes now consist of a list
            of child nodes only.
            
            Defines a new scope.
        """
        self.scopeStack.enterScope(node)
        self.nodeStack.append(node)
        if node.block_items == []:
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
                self.visit(currentItem)
                self.dynaMem.tick(currentItem.coord.line)
                for block in self.dynaMem.expiredBlocks():
                    self.warnings.append((block.lineAllocated,"Block allocated on line {0} not tested for successful allocation within {1} statements.".format(block.lineAllocated, dynamicMemory.checkThreshold)))

                if className(currentItem) in ["Decl"]:
                    for previousDecl in previousDecls:
                        if currentItem.coord.line == previousDecl.coord.line and\
                        (self.scopeStack.getVariableType(currentItem.name).isPointer() !=
                        self.scopeStack.getVariableType(previousDecl.name).isPointer()):
                            lineNum.append((currentItem.coord.line,self.scopeStack.getVariableType(currentItem.name).base))
                    previousDecls.append(currentItem)

            # Iterate through the distinct line numbers and report the warnings
            # We do not currently use j, the base type
            for (i,j) in set(lineNum):
                self.warnings.append((i, 'Mixed pointer and non-pointer declaration.'))
        #self.dynaMem.display("Exiting compound node.")
        self.scopeStack.exitScope()
        self.nodeStack.pop()

    def visit_FileAST(self, node): #Vital assumption: This node is only visited once during any execution
        """ Defines a new (highest) scope.      
        """
        if node == None:
            print 'None passed as node in visit_FileAST'
            return
        # it will traverse as normal, but skipping the main function at first
        self.scopeStack.enterScope(node)
        self.nodeStack.append(node)
        for (childname, child) in node.children():
            self.visit(child)
        self.nodeStack.pop()
        self.scopeStack.exitScope()
        
    def visit_FuncDef(self, node):
        """ Defines a new scope
        """
        if node == None:
            print 'None passed as node in visit_FuncDef'
            return
        self.scopeStack.enterScope(node)
        oldfunction = self.currentFunction
        self.currentFunction = node.decl.name
        self.returnEncountered = False
        self.generic_visit(node)
        #self.dynaMem.warnUnfreedBlocks(node.coord.line)
        #This is where we should warn about unfreed blocks
        for block in self.dynaMem.unfreedBlocks():
            self.warnings.append((block.lineAllocated, "Potential memory leak: Memory block allocated at line {0} has not been freed.".format(block.lineAllocated)))
        if not self.returnEncountered and not (className(node.decl.type.type) == 'TypeDecl'
                                        and className(node.decl.type.type.type) == 'IdentifierType'
                                        and node.decl.type.type.type.names[0] == 'void'):
            self.warnings.append((node.coord.line, "Function with non-VOID return type missing a return statement."))
        self.dynaMem.purge()
        self.currentFunction = oldfunction
        self.scopeStack.exitScope()

    def visit_FuncDecl(self, node):
        """ This is called upon visiting a function declaration.
        """
        self.generic_visit(node)

    def visit_FuncCall(self,node):
        """ ...
        """
        if node == None:
            print 'None passed as node in visit_FuncCall'
            return

        if className(node.name) == "ID":
            if node.name.name in dynamicMemory.uncheckedAllocators:
                if self.parentName() == "Assignment":
                    self.dynaMem.initializePointer(node.coord.line, getPointerID(self.nodeStack[-1].lvalue), False)
                elif self.parentName() == "Decl":
                    self.dynaMem.initializePointer(node.coord.line, getCType(self.nodeStack[-1]).getName())
                else:
                    self.warnings.append((node.name.coord.line,'Return value of dynamic memory allocator not assigned'))
            elif node.name.name in dynamicMemory.checkedAllocators:
                if self.parentName() == "Assignment":
                    self.dynaMem.initializePointer(node.coord.line, getPointerID(self.nodeStack[-1].lvalue), True)
                elif self.parentName() == "Decl":
                    self.dynaMem.initializePointer(node.coord.line, getCType(self.nodeStack[-1]).getName())
                else:
                    self.warnings.append((node.name.coord.line,'Return value of dynamic memory allocator not assigned'))
            elif node.name.name == "free":
                pointerID = node.args.exprs[0].name
                # pointer points to something
                if pointerID in self.dynaMem.pointerTarget:
                    if self.dynaMem.pointerTarget[pointerID].freed():
                        msg = 'Free called on pointer with previously freed target. Target previously freed at line %u.'%self.dynaMem.pointerTarget[pointerID].lineFreed
                        self.warnings.append((node.coord.line,msg))
                    else:
                        self.dynaMem.pointerTarget[pointerID].free(node.coord.line)
                        # Check to see if other pointers exist...
                        #msg = 'Call to free results in dangling pointers %s' %(retvals[1])
                        if self.dynaMem.pointerTarget[pointerID].pointers != empty_set:
                            msg = 'Call to free results in dangling pointers %s' %(pointerID)
                            

                # pointerID does not point to a block
                else:
                    msg = 'Free called on unallocated pointer \'%s\''%pointerID
                    self.warnings.append((node.coord.line,msg))
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
            if node.iftrue.block_items == None:
                self.warnings.append((node.coord.line,'Empty if block'))
        if node.iffalse!= None:
            if (className(node.iffalse) == 'Compound'):
                 if node.iffalse.block_items == None:
                    self.warnings.append((node.coord.line,'Empty else block'))
        self.generic_visit(node)
        if node.cond != None:
            if className(node.cond) == "Assignment"\
            and className(node.cond.rvalue) == "FuncCall" and node.cond.rvalue.name.name in dynamicMemory.uncheckedAllocators:
                self.dynaMem.check(node.coord.line, node.cond.lvalue.name)                                           # if(p=malloc(5)){return 42;}
            elif className(node.cond) == "UnaryOp" and node.cond.op == "!"\
            and className(node.cond.expr) == "Assignment"\
            and className(node.cond.expr.rvalue) == "FuncCall" and node.cond.expr.rvalue.name.name in dynamicMemory.uncheckedAllocators:
                self.dynaMem.check(node.coord.line, node.cond.lvalue.name)                                           # if(p=malloc(5)){return 42;}
            elif className(node.cond) == "ID":
                self.dynaMem.check(node.coord.line, node.cond.name)   #if(p) printf("foo")
            elif className(node.cond) == "UnaryOp" and node.cond.op == "!"\
            and className(node.cond.expr) == "ID":
                self.dynaMem.check(node.coord.line, node.cond.name)                                             # if(!p) printf("76")

    def visit_While(self, node):
        """ The individualized traversing code for While nodes.
            We can check for empty code blocks, off-by-one errors,
            and such.
        """
        if node == None:
            print 'None passed as node in visit_While'
            return

        #Loops have the possibility of having a single node for node.stmt,
        # e.g. while (true) i++;
        if node.stmt == None or (className(node.stmt) == 'Compound' and node.stmt.block_items == None):
        #if node.stmt == None or (node.stmt.block_itemss == None):
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
        if node.stmt == None or (className(node.stmt) == 'Compound' and node.stmt.block_items == None):
            self.warnings.append((node.coord.line,'Empty for block'))
        if node.init != None and node.cond != None and className(node.init) == "Assignment" and className(node.cond) == "BinaryOp":
            if className(node.init.rvalue) == "Constant" and node.init.rvalue.value == "0" and (node.cond.op == "<=" or node.cond.op == ">="):
                self.warnings.append((node.coord.line,'Possible off-by-one error in loop'))
            if className(node.init.rvalue) == "Constant" and node.init.rvalue.value == "1" and (node.cond.op == "<" or node.cond.op == ">"):
                self.warnings.append((node.coord.line,'Possible off-by-one error in loop'))
        self.generic_visit(node)

    def visit_Switch(self, node): # This code assumes that ; has been inserted after each case declaration using fixCase.py
        """ The custom traversing code for a Switch node.
            We can check for missing or inappropriate breaks or conditions.
        """
        if node == None:
            print 'None passed as node in visit_Switch'
            return
        if node.stmt == None or node.stmt.block_items == None:
            self.warnings.append((node.coord.line,'Empty switch statement block'))
        elif className(node.stmt) != "Compound":
            self.warnings.append((node.coord.line,'Single case statement in switch'))
            return
        else:
            # At this point, node.stmt is a Compound node
            stmtCount = len(node.stmt.block_items)
            caseIndices = []
            for i in range(stmtCount):
                if className(node.stmt.block_items[i]) in ['Case','Default']:
                    caseIndices.append(i)
            caseCount = len(caseIndices)
            for k in range(caseCount):
                stopIndex = stmtCount if k == caseCount-1 else caseIndices[k+1]
                breakFound = False
                for j in range(caseIndices[k]+1,stopIndex):
                    if className(node.stmt.block_items[j]) == 'Break':
                        breakFound = True
                        if j != stopIndex-1:
                            self.warnings.append((node.stmt.block_items[j].coord.line,
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

    def visit_Return(self, node):
        """ The custom code for traversing a return statement.
        """
        # Mark that we encountered a return statement
        self.returnEncountered = True
        if className(node.expr) == "ID":
            if self.dynaMem.pointsAtMemoryBlock(node.expr.name):
                # When we return a pointer to dynamically allocated memory from a function, we need
                # To make sure it won't issue an error as an unchecked/unfreed memory block
                #self.dynaMem.blank(node.expr.name)
                pointerID = node.expr.name
                self.dynaMem.pointerTarget[pointerID].lineFreed = node.coord.line
                self.dynaMem.pointerTarget[pointerID].lineChecked = node.coord.line
                self.dynaMem.pointerTarget[pointerID].pointers = set([]).copy()
                del(self.dynaMem.pointerTarget[pointerID])


if __name__ == "__main__":
    if len(sys.argv) == 2:
        filename = sys.argv[1]
        if not os.path.isfile(filename):
            print("error: "+filename+" cannot be read; does it exist?")
        else:
            print getWarnings(filename)
    else:
        print 'Arguments incorrect: should consist of the filename'
