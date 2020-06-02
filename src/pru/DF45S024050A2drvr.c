/* 
    This code assumes that it runs on pru 2_0. otherwise, the input and output registers are not
    used correctly
*/

#include <stdint.h>
#include <stdbool.h>
#include <pru_cfg.h>
#include "resource_table_empty.h"

#define ONESECOND (200000000)

volatile register uint32_t __R30;
volatile register uint32_t __R31;

#define GPO __R30
#define GPI __R31

#define BIT_IN_H1 (10)
#define BIT_IN_H2 (11)
#define BIT_IN_H3 (6)

#define BIT_OUT_UL (7)
#define BIT_OUT_VL (16)
#define BIT_OUT_WL (20)
#define BIT_OUT_UH (3)
#define BIT_OUT_VH (2)
#define BIT_OUT_WH (9)

static inline bool bGetGPI(int iBit)
{
    return (GPI & (1<<iBit));
}
static inline void bSetGPO(int iBit, bool bVal)
{
    if (bVal) { GPO |=  (1<<iBit);}
    else      { GPO &= ~(1<<iBit);}
}

static inline int iGetCommutationSeq()
{
    int iHallIdx = bGetGPI(BIT_IN_H1)+2*bGetGPI(BIT_IN_H2)+4*bGetGPI(BIT_IN_H3);
    int iSeq = -1;

    switch (iHallIdx)
    {
        case 1:     iSeq = 2;  break;//H1=1,H2=0,H3=0
        case 2:     iSeq = 0;  break;//H1=0,H2=1,H3=0
        case 3:     iSeq = 1;  break;//H1=1,H2=1,H3=0
        case 4:     iSeq = 4;  break;//H1=0,H2=0,H3=1
        case 5:     iSeq = 3;  break;//H1=1,H2=0,H3=1
        case 6:     iSeq = 5;  break;//H1=0,H2=1,H3=1
        default:    iSeq = -1; break;//this is an error!
    }

    return iSeq;
}

static inline void vEnableCoils(int iSeq, bool *bUL, bool *bVL, bool *bWL, bool *bUH, bool *bVH, bool *bWH)
{
    *bUH = (iSeq == 0) || (iSeq == 5);
    *bUL = (iSeq == 2) || (iSeq == 3);

    *bVH = (iSeq == 3) || (iSeq == 4);
    *bVL = (iSeq == 0) || (iSeq == 1);

    *bWH = (iSeq == 1) || (iSeq == 2);
    *bWL = (iSeq == 4) || (iSeq == 5);
}

static inline void vSetGPOs(bool bUL, bool bVL, bool bWL, bool bUH, bool bVH, bool bWH)
{
    bSetGPO(BIT_OUT_UL, bUL);
    bSetGPO(BIT_OUT_VL, bVL);
    bSetGPO(BIT_OUT_WL, bWL);
    bSetGPO(BIT_OUT_UH, bUH);
    bSetGPO(BIT_OUT_VH, bVH);
    bSetGPO(BIT_OUT_WH, bWH);
}

void main(void)
{
    int iCommutationSeq;
    bool bUL, bVL, bWL, bUH, bVH, bWH;

    while(1) {
        //see https://de.nanotec.com/produkte/156-bldc-buerstenlose-dc-motoren/, 2.1
        iCommutationSeq = iGetCommutationSeq();
        vEnableCoils(iCommutationSeq, &bUL, &bVL, &bWL, &bUH, &bVH, &bWH);
        vSetGPOs(bUL, bVL, bWL, bUH, bVH, bWH);


        //__delay_cycles(ONESECOND/100000);
    }
}
