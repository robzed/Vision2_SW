/* 
 * File:   timer_interrupts.h
 * Author: Rob Probin
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
bool is_timer_still_moving(void);
void timer_fine_to_move_another_cell(void);

void disable_IR_scanning(void);
void enable_IR_scanning(void);

void reset_wall_edge_flag(void);

void set_cell_distance(int);	//adjust these values for cell distance		
int get_cell_distance();

void set_wall_edge_to_crt_distance(int); //front error correction value
								//should equal distance from wall edge to
								//centre of square 
int get_wall_edge_to_crt_distance();

void set_front_long_threshold(int);		// is there a wall far away - used for moving ahead on explore
void set_front_short_threshold(int);     // front wall detection (also stops steering problems on turn)
void set_left_side_threshold(int);    // side wall detection
void set_right_side_threshold(int);    // side wall detection
void set_right_45_threshold(int);   // steering
void set_left_45_threshold(int);   // steering
void set_right_45_too_close_threshold(int);          // gross steering
void set_left_45_too_close_threshold(int);    // gross steering

int get_ir_front_side_bitmap();
int get_ir_45_bitmap(void);

void set_distance_to_test(int distance);
int get_distance_to_test();
int get_distance_test_flag(void);

// report data available as external variables
extern volatile char trim_report;

extern volatile int left_speed_sample;
extern volatile int right_speed_sample;
extern volatile char speed_sample_report;


#ifdef	__cplusplus
}
#endif

#endif	/* TIMER_INTERRUPTS_H */

