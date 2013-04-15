/* 
	This should be danglingPtr.html
	instead it stack-dumps	
*/

#include <stdio.h>
#include <stdlib.h>

int main(){ 	
	
	int *p1, *p2;
	
	p1 = malloc(20 * sizeof(int));  //Allocate array for 20 integers
	
	if(!p1){
		return EXIT_FAILURE;
	}
	
	p2 = p1;   //p1 and p2 point to the same allocated block of memory
	
	free(p1);  //this call leaves p2 dangling

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

