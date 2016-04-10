/* 
 * File:   timer_interrupts.h
 * Author: Rob Probin
 * Mostly copied from V_r100.c, created by Barry Grubb
 *
 * Created on April 10, 2016, 9:45 AM
 */

#ifndef TIMER_INTERRUPTS_H
#define	TIMER_INTERRUPTS_H

#ifdef	__cplusplus
extern "C" {
#endif

void init_timer1(void);
void init_timer2(void);
void init_timer3(void);
void init_timer4(void);
void init_adc(void);
unsigned int adc_read(unsigned int chan);
//void battery_check(void);
void sensor_select(void);



#ifdef	__cplusplus
}
#endif

#endif	/* TIMER_INTERRUPTS_H */

