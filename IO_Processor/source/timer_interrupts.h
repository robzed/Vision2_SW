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

#include <stdint.h>
#include <stdbool.h>

void init_timer_subsystems(void);

void timer_move(int distance, unsigned int speed, int steering_corrector);
bool is_timer_finished_move(void);
void timer_fine_to_move_another_cell(void);

void disable_IR_scanning(void);
void enable_IR_scanning(void);

#ifdef	__cplusplus
}
#endif

#endif	/* TIMER_INTERRUPTS_H */

