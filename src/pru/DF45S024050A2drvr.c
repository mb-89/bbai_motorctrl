/* 
    This code assumes that it runs on pru 2_0. otherwise, the input and output registers are not
    used correctly
*/

#include <stdint.h>
#include <stdbool.h>
#include <pru_cfg.h>
#include <pru_iep.h>
#include "resource_table_empty.h"

#define ONESECOND (200000000)
#define TENUSEC  ((ONESECOND/100000) - (120/5))
#define CLKDIV (20)

volatile register uint32_t __R30;
volatile register uint32_t __R31;
#define OFFSET_LOCALSHMEM (0x00000000)
#define __GPO__ __R30
#define __GPI__ __R31

#define CTRLMODE_IDLE (0)
#define CTRLMODE_COMU (1)
#define CTRLMODE_OPEN (2)
#define CTRLMODE_CLSD (3)

#define BIT_IN_H1 (1<<10) //P8_03, green wire
#define BIT_IN_H2 (1<<11) //P8_04, blue wire
#define BIT_IN_H3 (1<<6)  //P8_05, white wire

#define BIT_OUT_VH (1<<3)       /*P8_20*/
#define BIT_OUT_WE (1<<2)       /*P8_21*/
#define BIT_OUT_WH (1<<9)       /*P8_22*/
#define BIT_OUT_UE (1<<5)       /*P8_24*/
#define BIT_OUT_UH (1<<4)       /*P8_25*/
#define BIT_OUT_VE (1<<11)      /*P8_31*/
#define BIT_OUT_CPULOAD (1<<8)  /*P8_23*/

#define UHVL (BIT_OUT_UE|BIT_OUT_UH|BIT_OUT_VE)
#define WHVL (BIT_OUT_WE|BIT_OUT_WH|BIT_OUT_VE)
#define WHUL (BIT_OUT_WE|BIT_OUT_WH|BIT_OUT_UE)
#define VHUL (BIT_OUT_VE|BIT_OUT_VH|BIT_OUT_UE)
#define VHWL (BIT_OUT_VE|BIT_OUT_VH|BIT_OUT_WE)
#define UHWL (BIT_OUT_UE|BIT_OUT_UH|BIT_OUT_WE)
#define UVWL (BIT_OUT_UE|BIT_OUT_VE|BIT_OUT_WE)

#define ANGLE_360DEG (62832) //angle in rad*10000
#define ANGLE_180DEG (31416) //angle in rad*10000
#define ANGLE_60DEG (10472) //angle in rad*10000
#define ANGLE_30DEG (5236)  //angle in rad*10000

#define STATE_H1 (1<<0)
#define STATE_H2 (1<<1)
#define STATE_H3 (1<<2)

#define STATE_UE (1<<3)
#define STATE_UH (1<<4)
#define STATE_VE (1<<5)
#define STATE_VH (1<<6)
#define STATE_WE (1<<7)
#define STATE_WH (1<<8)

#define STATE_UHVL (STATE_UE|STATE_UH|STATE_VE)
#define STATE_WHVL (STATE_WE|STATE_WH|STATE_VE)
#define STATE_WHUL (STATE_WE|STATE_WH|STATE_UE)
#define STATE_VHUL (STATE_VE|STATE_VH|STATE_UE)
#define STATE_VHWL (STATE_VE|STATE_VH|STATE_WE)
#define STATE_UHWL (STATE_UE|STATE_UH|STATE_WE)
#define STATE_UVWL (STATE_UE|STATE_VE|STATE_WE)

static inline int Pos_iGetEl(int * iState)
{
    int iTmp = __GPI__;
    int iHallIdx =  iTmp&(BIT_IN_H1|BIT_IN_H2|BIT_IN_H3);
    int iAngle;

    switch (iHallIdx)
    {
        case BIT_IN_H3:             iAngle = ANGLE_60DEG*0 + ANGLE_30DEG; *iState |= STATE_H3;          break;
        case BIT_IN_H3|BIT_IN_H1:   iAngle = ANGLE_60DEG*1 + ANGLE_30DEG; *iState |= STATE_H3|STATE_H1; break;
        case BIT_IN_H1:             iAngle = ANGLE_60DEG*2 + ANGLE_30DEG; *iState |= STATE_H1;          break;
        case BIT_IN_H2|BIT_IN_H1:   iAngle = ANGLE_60DEG*3 + ANGLE_30DEG; *iState |= STATE_H2|STATE_H1; break;
        case BIT_IN_H2:             iAngle = ANGLE_60DEG*4 + ANGLE_30DEG; *iState |= STATE_H2;          break;
        case BIT_IN_H2|BIT_IN_H3:   iAngle = ANGLE_60DEG*5 + ANGLE_30DEG; *iState |= STATE_H2|STATE_H3; break;
        
        default:                    iAngle = 0;  break;//this is an error!
    }

    return iAngle;
}
static inline void Pos_vGetMech(int iNewElPos, bool bInit, int *OUT_iAngleMech, int *OUT_iAngPosMech)
{
    static int iOldElPos = 0;
    if (bInit){iOldElPos = 0;}

    int iDiff = iNewElPos-iOldElPos;
    if  (iDiff<-ANGLE_180DEG)       {iDiff+=ANGLE_360DEG;}
    else if (iDiff>ANGLE_180DEG)    {iDiff-=ANGLE_360DEG;}
    iOldElPos = iNewElPos;
    *OUT_iAngPosMech += iDiff/8;
    *OUT_iAngleMech += iDiff/8;
    if      (*OUT_iAngleMech<0)            {*OUT_iAngleMech+=ANGLE_360DEG;}
    else if (*OUT_iAngleMech>ANGLE_360DEG) {*OUT_iAngleMech-=ANGLE_360DEG;}
}

static inline void Cycle_vEnableCnt()
{
    CT_CFG.CGR_bit.IEP_CLK_EN       = 1;
    CT_IEP.GLB_CFG_bit.CNT_ENABLE   = 1;
    CT_IEP.GLB_CFG_bit.CMP_INC      = 1;
    CT_IEP.GLB_CFG_bit.DEFAULT_INC  = 1;
}
static inline void Cycle_vWait4Next()
{
    __GPO__ |= BIT_OUT_CPULOAD;
    while(CT_IEP.LOW_COUNTER<TENUSEC){}
    __GPO__ &=~BIT_OUT_CPULOAD;
    CT_IEP.LOW_COUNTER = 0;
}

static inline void vCommutate(int iPhase, int * iState)
{
    uint32_t iTmp = __GPO__;
    //clear all bits (locally)
    iTmp &= ~(BIT_OUT_UE|BIT_OUT_UH|BIT_OUT_VE|BIT_OUT_VH|BIT_OUT_WE|BIT_OUT_WH);
    //set the bits that belong to the current 
    
    switch (iPhase)
    {
        default:
        case 0: break;                                      //0 = idle, clear all

        case 1: iTmp |= WHVL; *iState |= STATE_WHVL; break;//phase for angle 0-60    @CW
        case 2: iTmp |= UHVL; *iState |= STATE_UHVL; break;//phase for angle 60-120  @CW
        case 3: iTmp |= UHWL; *iState |= STATE_UHWL; break;//phase for angle 120-180 @CW
        case 4: iTmp |= VHWL; *iState |= STATE_VHWL; break;//phase for angle 180-240 @CW
        case 5: iTmp |= VHUL; *iState |= STATE_VHUL; break;//phase for angle 240-300 @CW
        case 6: iTmp |= WHUL; *iState |= STATE_WHUL; break;//phase for angle 300-360 @CW

        case -1: iTmp |= UVWL; *iState |= STATE_UVWL;break;//special case for eddy-brake: short the windings to 0
    }
    __GPO__ = iTmp;
}
static inline int iElAngle2Phase(iAngle)
{
    if      (iAngle<ANGLE_60DEG)    {return 1;}
    else if (iAngle<2*ANGLE_60DEG)  {return 2;}
    else if (iAngle<3*ANGLE_60DEG)  {return 3;}
    else if (iAngle<4*ANGLE_60DEG)  {return 4;}
    else if (iAngle<5*ANGLE_60DEG)  {return 5;}
    else if (iAngle<6*ANGLE_60DEG)  {return 6;}
    else                            {return 0;}
}

static inline void CtrlMode_vIdle(int * iState)
{
    vCommutate(0, iState);
}
static inline void CtrlMode_vCommutate(int iPhase, int * iState)
{
    vCommutate(iPhase, iState);
}
static inline void CtrlMode_vOpenLoopSpd(int iClkDiv, int * iState)
{
    static int iLastPos = 1;
    static int iLastClk = 0;
    if (iLastClk == 0)
    {
        if (iClkDiv<1){iClkDiv = 1;}
        iLastClk =5000/iClkDiv;

        iLastPos++;
        if (iLastPos > 6) iLastPos=1;
        vCommutate(iLastPos, iState);
    }
    iLastClk -=1;
}
static inline void CtrlMode_vClosedLoopSpd(int iClkDiv, int iAngleEl, int * iState)
{
    static int iLastClk = 0;
    int iPhase = 0;
    if (iLastClk == 0)
    {
        if (iClkDiv<1){iClkDiv = 1;}
        iLastClk =5000/iClkDiv;


        if      (iAngleEl<ANGLE_60DEG)    {iPhase = 1;}
        else if (iAngleEl<2*ANGLE_60DEG)  {iPhase = 2;}
        else if (iAngleEl<3*ANGLE_60DEG)  {iPhase = 3;}
        else if (iAngleEl<4*ANGLE_60DEG)  {iPhase = 4;}
        else if (iAngleEl<5*ANGLE_60DEG)  {iPhase = 5;}
        else if (iAngleEl<6*ANGLE_60DEG)  {iPhase = 6;}
        else                              {iPhase = 0;}

        vCommutate(iPhase, iState);
    }
    iLastClk -=1;
}

void main(void)
{
    int iAngleEl = 0;
    int iAngleMech = 0;
    int iAngPosMech = 0;
    int iClkDiv = 0;
    int iState = 0;
    int iOldState = 0;
    int iIncs = 0;
    volatile int iCtrlMode = 0;
    uint32_t *shmem = (uint32_t *) OFFSET_LOCALSHMEM;

    Cycle_vEnableCnt();
    iAngleEl        = Pos_iGetEl(&iState);
    Pos_vGetMech(iAngleEl, true, &iAngleMech, &iAngPosMech);

    shmem[2] = 0; //contains the control mode
    shmem[3] = 0; //contains the first reference val

    while(1) {
        iState = 0;
        iAngleEl = Pos_iGetEl(&iState);
        if (iState != iOldState) iIncs++;
        iOldState = iState;
        Pos_vGetMech(iAngleEl, false, &iAngleMech, &iAngPosMech);
        
        if (--iClkDiv <= 0) //we can only switch with a limited freqency (here: use 5k for now)
        {
            iCtrlMode = shmem[2];
            switch (iCtrlMode)
            {
                default:
                case CTRLMODE_IDLE: CtrlMode_vIdle(&iState);                                break;
                case CTRLMODE_COMU: CtrlMode_vCommutate(shmem[3],&iState);                  break;
                case CTRLMODE_OPEN: CtrlMode_vOpenLoopSpd(shmem[3],&iState);                break;
                case CTRLMODE_CLSD: CtrlMode_vClosedLoopSpd(shmem[3],iAngleEl, &iState);    break;
            }

            iClkDiv = CLKDIV; //20*10usec = 200 usec = 5kHz

            //write output to sharedmem. we dont need to do this in every cycle
            shmem[0] = iAngleEl;
            shmem[1] = iIncs;
        }

        Cycle_vWait4Next();
    }
}
