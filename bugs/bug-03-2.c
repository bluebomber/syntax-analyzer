/* 
	While for other functions an exit doesn't boil down to the same as a return, 
	this should be allowed for main without triggering any "missing return for 
	non-void function" warnings
*/ 

#include <stdlib.h>
#include <stdio.h>
int main(){
	int n; 
	
	n = 42;

	printf("Result is %d\n", n); 
	
	exit(EXIT_SUCCESS);
}

