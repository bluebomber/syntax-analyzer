/*
	should trigger PointerToConstant.html / pointers-to-constants.php 
*/

#include <stdio.h>
#include <stdlib.h>

int main(){
	char *s;
	s = "Jim is my name";
	printf("%s\n",s);

	s[0] = 'K';
	printf("%s\n",s);
	
	return EXIT_SUCCESS;
}

