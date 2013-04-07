/*
 *
 *  should trigger shadowing.html or ShadowedVariable.html
 *
 *  */ 



#include <stdio.h>

#include <stdlib.h> 



int main(){
    int n = 0;
    printf("Initially\tn = %d\n", n);
    if( 42 > 0){
        int n = 5;
        n++;
        printf("Inside loop\tn = %d\n", n);
    }
    printf("After loop\tn = %d\n", n);  
    return EXIT_SUCCESS;
}


