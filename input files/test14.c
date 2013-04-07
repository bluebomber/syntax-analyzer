/* 
 *
 *  This results in call to free results in dangling pointers p1
 *
 *      even though p1 is assigned to NULL after being free
 *
 *      */

#include <stdlib.h>



int main(){
    int * p1 = NULL;
    p1 = malloc(sizeof(int));
    //we should make sure p1 is not NULL here before to proceed    
    free(p1);
    p1 = NULL;
    return EXIT_SUCCESS;
}
