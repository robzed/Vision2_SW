/*
 * File:   configuration_bits.c
 * Author: Rob Probin
 *
 * Created on 27 June 2014, 20:14
 */

#include <p30F4011.h>

_FOSC(CSW_FSCM_OFF & XT_PLL8);  // XT with 8xPLL, Failsafe clock off
_FWDT(WDT_OFF);                 // Watchdog timer disabled
_FBORPOR(PBOR_OFF & MCLR_EN);   // Brown-out reset disabled, MCLR pin enabled
_FGS(CODE_PROT_OFF);
