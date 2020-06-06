/* 
    This code assumes that it runs on pru 2_0. otherwise, the input and output registers are not
    used correctly
*/

#include <stdint.h>
#include <stdbool.h>
#include <pru_cfg.h>
#include "resource_table_empty.h"

#define ONESECOND (200000000)

#define OFFSET_LOCALSHMEM (0x00000000)
#define OFFSET_BIT_UL (1<<0)
#define OFFSET_BIT_VL (1<<1)
#define OFFSET_BIT_WL (1<<2)
#define OFFSET_BIT_UH (1<<3)
#define OFFSET_BIT_VH (1<<4)
#define OFFSET_BIT_WH (1<<5)

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

#define BIT_OUT_CPULOAD (8)

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

static inline uint32_t iEnableCoils(int iSeq)
{
    uint32_t iTmp = 0;

    iTmp |= ((iSeq == 0) || (iSeq == 5)) * OFFSET_BIT_UH;
    iTmp |= ((iSeq == 2) || (iSeq == 3)) * OFFSET_BIT_UL;

    iTmp |= ((iSeq == 3) || (iSeq == 4)) * OFFSET_BIT_VH;
    iTmp |= ((iSeq == 0) || (iSeq == 1)) * OFFSET_BIT_VL;

    iTmp |= ((iSeq == 1) || (iSeq == 2)) * OFFSET_BIT_WH;
    iTmp |= ((iSeq == 4) || (iSeq == 5)) * OFFSET_BIT_WL;

    return iTmp;
}

static inline void vSetGPOs(uint32_t iCommutationBits)
{
    bSetGPO(BIT_OUT_UL, iCommutationBits&OFFSET_BIT_UL);
    bSetGPO(BIT_OUT_VL, iCommutationBits&OFFSET_BIT_VL);
    bSetGPO(BIT_OUT_WL, iCommutationBits&OFFSET_BIT_WL);
    bSetGPO(BIT_OUT_UH, iCommutationBits&OFFSET_BIT_UH);
    bSetGPO(BIT_OUT_VH, iCommutationBits&OFFSET_BIT_VH);
    bSetGPO(BIT_OUT_WH, iCommutationBits&OFFSET_BIT_WH);
}

static inline int iGetPosDiff(int iNewSeq)
{
    static int iOldSeq = 0;

    bool CntUp  = (iNewSeq>iOldSeq) || (iNewSeq==0 && iOldSeq == 5);
    bool CntDown= (iNewSeq<iOldSeq) || (iNewSeq==5 && iOldSeq == 0);
    iOldSeq = iNewSeq;

    int iDiff = CntUp ? 1 : CntDown ? -1 : 0;
    return iDiff;
}

void main(void)
{
    int iCommutationSeq;
    int iPos;

    uint32_t iCommutationBits;
    uint32_t *shmem = (uint32_t *) OFFSET_LOCALSHMEM;

    iCommutationSeq = iGetCommutationSeq();
    iGetPosDiff(iCommutationSeq);
    iPos = 0;

    bool bCPULoad = false;

    while(1) {
        //see https://de.nanotec.com/produkte/156-bldc-buerstenlose-dc-motoren/, 2.1
        iCommutationSeq = iGetCommutationSeq();
        iPos += iGetPosDiff(iCommutationSeq);
        iCommutationBits = iEnableCoils(iCommutationSeq);
        vSetGPOs(iCommutationBits);

        //write output to sharedmem
        shmem[0] = iCommutationBits;
        shmem[1] = iPos;

        bSetGPO(BIT_OUT_CPULOAD, bCPULoad);
        bCPULoad = !bCPULoad;
        //__delay_cycles(ONESECOND/100000);
    }
}
