/* 
 * File:   io_ports.h
 * Author: Rob Probin
 *
 * Created on 29 June 2014, 11:16
 */

#ifndef IO_PORTS_H
#define	IO_PORTS_H

#include <p30F4011.h>

// port definitions, taken from Barry Grubb's code

// LED output ports
#define led_front       LATEbits.LATE0
#define led_left        LATEbits.LATE1
#define led_right       LATFbits.LATF0
#define led1            LATFbits.LATF1
#define led2            LATFbits.LATF4
#define led3            LATFbits.LATF5
#define led4            LATEbits.LATE3
#define led5            LATEbits.LATE4
#define led6            LATEbits.LATE5

// output ports for IR LEDs
#define irled_front     LATBbits.LATB8
#define irled_90        LATBbits.LATB7
#define irled_45        LATBbits.LATB6

// ports for buttons
#define grey_button     PORTEbits.RE2
#define blue_button     PORTEbits.RE8

// output ports for motor control
#define en_mot          LATFbits.LATF6
#define clk_l           LATDbits.LATD3
#define clk_r           LATDbits.LATD2
#define dir_l           LATDbits.LATD1
#define dir_r           LATDbits.LATD0

// general on/off uses positive logic
#define on	1
#define off	0

// en motors are negative logic
#define mot_on 0
#define mot_off 1

// Analogue input channels
#define r90 0
#define r45 1
#define fr  2
#define l45 3
#define l90 4
#define bat 5



#endif	/* IO_PORTS_H */

