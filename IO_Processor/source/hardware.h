/* 
 * File:   hardware.h
 * Author: rob
 *
 * Created on 27 June 2014, 21:29
 */

#ifndef HARDWARE_H
#define	HARDWARE_H

#include "io_ports.h"
#include <stdint.h>
#include <stdbool.h>

//
// IO that looks like functions
//

// Buttons
#define Grey_A_ButtonPressed() (!grey_button)
#define Blue_B_ButtonPressed() (!blue_button)

// Combinations of directions
#define fwd()           (dir_l=1,dir_r=0)
#define rev()           (dir_l=0,dir_r=1)
#define turnl()         (dir_l=0,dir_r=0)
#define turnr()         (dir_l=1,dir_r=1)


void ConfigureOscillator(void);
void InitPorts();
void InitPeripherals();
void AllLedsOff(void);
void LedOn(int led);
void delay_ms(unsigned int ms_count);
unsigned int adc_read(unsigned int chan);

// Input definition for read_sensor
enum {
    front = 1,
    side = 2,
    diag = 3
};
void read_sensor(char sensor);


// serial routines
void serial_write_string(char* s);
void serial_write_data(uint8_t* s, int l);
void serial_write_char(char c);
void serial_write_uint8(uint8_t byte);
void serial_write_int16(int16_t data);
void serial_flush(void);
bool serial_byte_waiting();
int serial_get_byte();
int serial_get_char();


#endif	/* HARDWARE_H */

