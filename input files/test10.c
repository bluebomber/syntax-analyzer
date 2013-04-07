/* 
 *
 *  This should trigger BreakInMiddle.html, it goes underected by SyntaxParser.py
 *
 *  */ 



#include <stdlib.h>

#include <stdio.h>



int main(){
    int i=0;
    switch (i)
    {
    case 0:
    i ++;
    break;
    printf("I will never be executed\n");
    default:
    break;
    }
    return EXIT_SUCCESS;
}
