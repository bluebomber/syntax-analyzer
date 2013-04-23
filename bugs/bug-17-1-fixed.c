/* 
	There is a tutorial on this; NoBreak.html / missing-break.php
	but nothing is detected
*/

#include <stdio.h>
#include <time.h>
#include <stdlib.h>

int main(){
	srand(time(NULL)); 
	int n = rand()%10;
	
	printf("The random number %d is a ", n);
	
	switch(n){
		case 0:
			printf("null");
		case 2:
		case 4: 
		case 6: 
		case 8: 
			printf("even"); 
			break;
		case 1:
		case 3: 
		case 5: 
		case 7: 
		case 9: 
			printf("odd");
			break;
		default:
			printf("out of range");
	}	
	
	printf(" number\n");
	
	return EXIT_SUCCESS;
}

