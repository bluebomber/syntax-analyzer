/* 
	this should find DoubleFree.html
	stack dumps instead
*/
#include <stdlib.h>

int main(){
	int *p1 = NULL, *p2 = NULL;
	
	p1 = malloc(sizeof(int)); 
	if(!p1){
		return EXIT_FAILURE;
	}
	
	p2 = p1;	// both pointers refer to the same memory block
	
	free(p1);	// freeing the memory block
	free(p2); // freeing the same memory block again

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
 
File "/var/www/ned/analyzers/SyntaxAnalyzer.py", line 714, in visit_If
 
self.dynaMem.check(node.coord.line, node.cond.name) # if(!p) printf("76")
 
AttributeError: 'UnaryOp' object has no attribute 'name'
*/

