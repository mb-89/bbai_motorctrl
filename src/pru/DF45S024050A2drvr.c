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

static inline int Pos_iGetEl()
{
    int iTmp = __GPI__;
    int iHallIdx =  iTmp&(BIT_IN_H1|BIT_IN_H2|BIT_IN_H3);
    int iAngle;

    switch (iHallIdx)
    {
        case BIT_IN_H2:             iAngle = ANGLE_60DEG*0 + ANGLE_30DEG;  break;
        case BIT_IN_H2|BIT_IN_H1:   iAngle = ANGLE_60DEG*1 + ANGLE_30DEG;  break;
        case BIT_IN_H1:             iAngle = ANGLE_60DEG*2 + ANGLE_30DEG;  break;
        case BIT_IN_H1|BIT_IN_H3:   iAngle = ANGLE_60DEG*3 + ANGLE_30DEG;  break;
        case BIT_IN_H3:             iAngle = ANGLE_60DEG*4 + ANGLE_30DEG;  break;
        case BIT_IN_H3|BIT_IN_H2:   iAngle = ANGLE_60DEG*5 + ANGLE_30DEG;  break;

        default:                    iAngle = 0;  break;//this is an error!
    }

    return iAngle;
}
static inline int Pos_iGetMech(int iNewElPos, bool bInit)
{
    static int iOldElPos = 0;
    static int iOldMechPos = 0;
    
    if (bInit)
    {
        iOldMechPos=0;
        iOldElPos = 0;
    }

    int iDiff = iNewElPos-iOldElPos;
    if  (iDiff<-ANGLE_180DEG)       {iDiff+=ANGLE_360DEG;}
    else if (iDiff>ANGLE_180DEG)    {iDiff-=ANGLE_360DEG;}
    iOldElPos = iNewElPos;
    iOldMechPos += iDiff/8;

    return iOldMechPos;
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

static inline void vCommutate(int iPhase)
{
    uint32_t iTmp = __GPO__;
    //clear all bits (locally)
    iTmp &= ~(BIT_OUT_UE|BIT_OUT_UH|BIT_OUT_VE|BIT_OUT_VH|BIT_OUT_WE|BIT_OUT_WH);
    //set the bits that belong to the current 
    
    switch (iPhase)
    {
        default:
        case 0: break;                                      //0 = idle, clear all

        case 1: iTmp |= UHVL; break;//phase for angle 0-60    @CW
        case 2: iTmp |= WHVL; break;//phase for angle 60-120  @CW
        case 3: iTmp |= WHUL; break;//phase for angle 120-180 @CW
        case 4: iTmp |= VHUL; break;//phase for angle 180-240 @CW
        case 5: iTmp |= VHWL; break;//phase for angle 240-300 @CW
        case 6: iTmp |= UHWL; break;//phase for angle 300-360 @CW

        case -1: iTmp |= UVWL; break;//special case for eddy-brake: short the windings to 0
    }
    __GPO__ = iTmp;
}
static inline int iAngle2Phase(iAngle)
{
    if      (iAngle<ANGLE_60DEG)    {return 1;}
    else if (iAngle<2*ANGLE_60DEG)  {return 2;}
    else if (iAngle<3*ANGLE_60DEG)  {return 3;}
    else if (iAngle<4*ANGLE_60DEG)  {return 4;}
    else if (iAngle<5*ANGLE_60DEG)  {return 5;}
    else if (iAngle<6*ANGLE_60DEG)  {return 6;}
    else                            {return 0;}
}

static inline void CtrlMode_vIdle()
{
    vCommutate(0);
}
static inline void CtrlMode_vCommutate(int iPhase)
{
    vCommutate(iPhase);
}
static inline void CtrlMode_vOpenLoopSpd(int iRpm)
{
    static int iLastPos = 0;
    iLastPos += ANGLE_360DEG*(CLKDIV*10)/(1000*1000)*iRpm;
    if (iLastPos > ANGLE_360DEG) iLastPos-=ANGLE_360DEG;
    vCommutate(iAngle2Phase(iLastPos));
}

static inline void CtrlMode_vClosedLoopSpd(int iAngleEl, int iRpm)
{
    vCommutate(iAngle2Phase(iAngleEl));
}

void main(void)
{
    int iAngleEl = 0;
    int iAngularPosMech = 0;
    int iClkDiv = 0;
    volatile int iCtrlMode = 0;
    uint32_t *shmem = (uint32_t *) OFFSET_LOCALSHMEM;

    Cycle_vEnableCnt();
    iAngleEl        = Pos_iGetEl();
    iAngularPosMech = Pos_iGetMech(iAngleEl, true);

    shmem[2] = 0; //contains the control mode
    shmem[3] = 0; //contains the first reference val

    while(1) {
        iAngleEl =          Pos_iGetEl();
        iAngularPosMech=    Pos_iGetMech(iAngleEl, false);
        
        if (--iClkDiv <= 0) //we can only switch with a limited freqency (here: use 5k for now)
        {
            iCtrlMode = shmem[2];
            switch (iCtrlMode)
            {
                default:
                case CTRLMODE_IDLE: CtrlMode_vIdle(); break;
                case CTRLMODE_COMU: CtrlMode_vCommutate(shmem[3]);                  break;
                case CTRLMODE_OPEN: CtrlMode_vOpenLoopSpd(shmem[3]);                break;
                case CTRLMODE_CLSD: CtrlMode_vClosedLoopSpd(iAngleEl, shmem[3]);    break;
            }

            iClkDiv = CLKDIV; //20*10usec = 200 usec = 5kHz

            //write output to sharedmem. we dont need to do this in every cycle
            shmem[0] = iAngleEl;
            shmem[1] = iAngularPosMech;
        }

        Cycle_vWait4Next();
    }
}
