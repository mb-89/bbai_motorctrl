#ifndef _PRU_GPIO_H_
#define _PRU_GPIO_H_

typedef struct {
    unsigned b0_P844 : 1;
    unsigned b1_P841 : 1;
    unsigned b2_P821_P842 : 1;
    unsigned b3_P820_P839 : 1;
    unsigned b4_P825_P840 : 1;
    unsigned b5_P824_P837 : 1;
    unsigned b6_P805_P838 : 1;
    unsigned b7_P806_P836 : 1;
    unsigned b8_P823_P834 : 1;
    unsigned b9_P822_P835 : 1;
    unsigned b10_P803_P833: 1;
    unsigned b11_P804_P831: 1;
    unsigned b12_P832: 1;
    unsigned b13_P845: 1;
    unsigned b14_P911: 1;
    unsigned b15_P817_P913: 1;
    unsigned b16_P827: 1;
    unsigned b17_P828: 1;
    unsigned b18_P829: 1;
    unsigned b19_P830: 1;
    unsigned b20_P808_P846: 1;
} pru20gpio;

#endif /* _PRU_GPIO_H_ */