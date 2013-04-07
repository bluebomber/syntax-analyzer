/* 
 *
 *  should trigger PointerNotInitialized.html / pointers-not-init.php
 *
 *  */



#include <stdlib.h>

int main(){
    int * p1 = NULL;
    int * p2;
    return EXIT_SUCCESS;
}
