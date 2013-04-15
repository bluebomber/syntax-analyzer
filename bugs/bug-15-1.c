/* 
	should detect SizeofPointer.html
	stack-dumps instead
*/

#include <stdio.h>
#include <stdlib.h>

int main(){
	int data[3]; 
	int * ptr = NULL; 
	int n; 
	
	ptr = malloc(sizeof(int) * 3); 
	if(!ptr) return EXIT_FAILURE; 
	
	for(n=0 ; n < 3 ; n++){ 
		data[n] = ptr[n] = 42; 
	}
	
	printf("Size of regular array is %d\n", (int)sizeof(data)); 
	// displays 12 i.e. the size of an array of 3 int
	
	printf("Size of dynamical array is not %d\n", (int)sizeof(ptr)); 
	// displays 4 i.e. the size of a pointer
	// regardless of what it is meant to point to
	
	printf("It is not %d either\n", (int)sizeof(*ptr)); 
	// displays 4 i.e. the size of an int
	
	free(ptr);
	
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
