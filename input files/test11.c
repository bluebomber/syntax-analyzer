/* 
 *
 *  This should be danglingPtr.html
 *
 *      instead it stack-dumps  
 *
 *      */



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
