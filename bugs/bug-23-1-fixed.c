/*
	should trigger mixedAssignments.html / pointers-mixed
*/ 

#include <stdlib.h> 

int main(){
	int *p1, p2, *p3; 
	
	return EXIT_SUCCESS;
}
/*
Traceback (most recent call last):
 
File "/var/www/ned/analyzers/SyntaxAnalyzer.py", line 1232, in
 
for id,w in getWarnings(file_name):
 
File "/var/www/ned/analyzers/SyntaxAnalyzer.py", line 1219, in getWarnings
 
s.visit(ast)
 
File "/usr/local/lib/python2.7/dist-packages/pycparser/c_ast.py", line 119, in visit
 
return visitor(node)
 
File "/var/www/ned/analyzers/SyntaxAnalyzer.py", line 1005, in visit_FileAST
 
self.visit(child)
 
File "/usr/local/lib/python2.7/dist-packages/pycparser/c_ast.py", line 119, in visit
 
return visitor(node)
 
File "/var/www/ned/analyzers/SyntaxAnalyzer.py", line 1019, in visit_FuncDef
 
self.generic_visit(node)
 
File "/var/www/ned/analyzers/SyntaxAnalyzer.py", line 807, in generic_visit
 
self.visit(child)
 
File "/usr/local/lib/python2.7/dist-packages/pycparser/c_ast.py", line 119, in visit
 
return visitor(node)
 
File "/var/www/ned/analyzers/SyntaxAnalyzer.py", line 984, in visit_Compound
 
lineNum.append((currentItem.coord.line,self.scopeStack.get_variable_type(currentItem.name).base))
 
AttributeError: CType instance has no attribute 'base' 
*/
