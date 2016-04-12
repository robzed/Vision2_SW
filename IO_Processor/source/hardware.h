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
void InitPorts(void);
void InitPeripherals(void);
void AllLedsOff(void);
void LedSwitch(int led, int state);
void delay_ms(unsigned int ms_count);
unsigned int adc_read(unsigned int chan);
void delay_us( unsigned int us_count );

void battery_check(void);
void key_scan(void);

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
unsigned int serial_get_uint16(void);
int serial_get_int16(void);


// Power on reset registers
#define POR             (RCONbits.POR == 1)
#define BOR             (RCONbits.BOR == 1)
#define WDTO            (RCONbits.WDTO == 1)
#define SWR             (RCONbits.SWR == 1)
#define EXTR            (RCONbits.EXTR == 1)
#define IOPUWR          (RCONbits.IOPUWR == 1)


extern unsigned int front_sensor;
extern unsigned int right_side_sensor;
extern unsigned int left_side_sensor;
extern unsigned int r45_sensor;
extern unsigned int l45_sensor;

extern volatile unsigned int battery_voltage;
extern volatile char battery_data_ready;

extern volatile char key_A_stored;
extern volatile char key_A_changed;

extern volatile char key_B_stored;
extern volatile char key_B_changed;

#endif	/* HARDWARE_H */

