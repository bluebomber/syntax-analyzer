/* 
 *
 *  should be identified as memoryLeak.html
 *
 *      stack-dumps instead
 *
 *      */



#include <stdlib.h>



int main(){
    int *p1, *p2;
    p1 = malloc(sizeof(int));
    p2 = malloc(sizeof(int));
    p2 = p1; // The block of memory allocated in the previous statement is now unrecoverable.
    return EXIT_SUCCESS;
}
