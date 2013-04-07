/* 
 *
 *   this should trigger a "empty code block"
 *
 *   */ 



#include <stdlib.h>
#include <stdio.h>



int main(){
    int n = 0;
    while(n < 42); /* infinite loop! */
    { printf("."); n++; }
    for(n=0 ; n < 42 ; n++); // another
    { printf("."); }
    return EXIT_SUCCESS; }
