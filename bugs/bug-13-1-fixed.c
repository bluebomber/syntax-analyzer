/* 
	should be identified as memoryLeak.html
	stack-dumps instead
*/

#include <stdlib.h>

int main(){
	int *p1, *p2;
	p1 = malloc(sizeof(int));
	p2 = malloc(sizeof(int));
	p2 = p1; // The block of memory allocated in the previous statement is now unrecoverable.
	return EXIT_SUCCESS;
}
/*
Traceback (most recent call last):
 
File "/var/www/ned/analyzers/SyntaxAnalyzer.py", line 1232, in
 
for id,w in getWarnings(file_name):
 
File "/var/www/ned/analyzers/SyntaxAnalyzer.py", line 1214, in getWarnings
 
AllocatorVisitor().visit(ast)
 
File "/usr/local/lib/python2.7/dist-packages/pycparser/c_ast.py", line 119, in visit
 
return visitor(node)
 
File "/var/www/ned/analyzers/SyntaxAnalyzer.py", line 667, in visit_FileAST
 
self.generic_visit(node)
 
File "/var/www/ned/analyzers/SyntaxAnalyzer.py", line 595, in generic_visit
 
self.visit(child)
 
File "/usr/local/lib/python2.7/dist-packages/pycparser/c_ast.py", line 119, in visit
 
return visitor(node)
 
File "/var/www/ned/analyzers/SyntaxAnalyzer.py", line 675, in visit_FuncDef
 
self.generic_visit(node)
 
File "/var/www/ned/analyzers/SyntaxAnalyzer.py", line 595, in generic_visit
 
self.visit(child)
 
File "/usr/local/lib/python2.7/dist-packages/pycparser/c_ast.py", line 119, in visit
 
return visitor(node)
 
File "/var/www/ned/analyzers/SyntaxAnalyzer.py", line 654, in visit_Compound
 
self.generic_visit(node)
 
File "/var/www/ned/analyzers/SyntaxAnalyzer.py", line 595, in generic_visit
 
self.visit(child)
 
File "/usr/local/lib/python2.7/dist-packages/pycparser/c_ast.py", line 119, in visit
 
return visitor(node)
 
File "/var/www/ned/analyzers/SyntaxAnalyzer.py", line 606, in visit_Assignment
 
self.dynaMem.copy_pointer(node.coord.line, node.lvalue.name, node.rvalue.name)
 
File "/var/www/ned/analyzers/SyntaxAnalyzer.py", line 460, in copy_pointer
 
self.link_pointer_to_block(pointerIDA, self.pointerTarget[pointerIDB])
 
File "/var/www/ned/analyzers/SyntaxAnalyzer.py", line 445, in link_pointer_to_block
 
self.blocks[blockID].add_pointer(pointerID)
 
TypeError: object cannot be interpreted as an index
*/
