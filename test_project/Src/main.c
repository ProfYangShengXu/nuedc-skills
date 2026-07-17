#include "main.h"

int main(void)
{
    volatile int i;
    while (1)
    {
        for (i = 0; i < 100000; i++);
        GPIOB->ODR ^= (1 << 0);
    }
}
