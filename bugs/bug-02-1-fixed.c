/* 
	empty function is a problem
*/ 

#include <stdlib.h>
#include <stdio.h>

int foo(){

}

int main(){
	int n; 
	
	n = foo(); 

	printf("Result is %d\n", n); 
	
	exit(EXIT_SUCCESS);
}

/* 
Traceback (most recent call last):
 
File "/var/www/ned/analyzers/SyntaxAnalyzer.py", line 1228, in
 
for id,w in getWarnings(file_name):
 
File "/var/www/ned/analyzers/SyntaxAnalyzer.py", line 1218, in getWarnings
 
s.visit(ast)
 
File "/usr/local/lib/python2.7/dist-packages/pycparser/c_ast.py", line 119, in visit
 
return visitor(node)
 
File "/var/www/ned/analyzers/SyntaxAnalyzer.py", line 1004, in visit_FileAST
 
self.visit(child)
 
File "/usr/local/lib/python2.7/dist-packages/pycparser/c_ast.py", line 119, in visit
 
return visitor(node)
 
File "/var/www/ned/analyzers/SyntaxAnalyzer.py", line 1018, in visit_FuncDef
 
self.generic_visit(node)
 
File "/var/www/ned/analyzers/SyntaxAnalyzer.py", line 806, in generic_visit
 
self.visit(child)
 
File "/usr/local/lib/python2.7/dist-packages/pycparser/c_ast.py", line 119, in visit
 
return visitor(node)
 
File "/var/www/ned/analyzers/SyntaxAnalyzer.py", line 973, in visit_Compound
 
for currentItem in node.block_items:
 
TypeError: 'NoneType' object is not iterable
*/

