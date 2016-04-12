/* 
 * File:   commands_ref.h
 * Author: Rob Probin
 *
 * Created on April 9, 2016, 10:19 AM
 */

#ifndef COMMANDS_REF_H
#define	COMMANDS_REF_H

#ifdef	__cplusplus
extern "C" {
#endif

// Overview:
//
// * dsPIC has 4 character tx+rx buffer, plus serial transmit+receive bugger
// * We don't use interrupt ... so sending lots of commands will crash the buffer.
// * These commands are designed to look like instructions, and be 1-4 bytes long
//
// * Events - from dsPIC to R-Pi
// * Commands - from R-Pi to dsPIC
//
// * ‘Dangerous’ Commands from the R-Pi should have some sort of check on them.
// * If the dsPIC doesn’t hear for 100ms from the R-Pi it should lock to avoid spurious invalid commands.
// *
// * At 57600 we get a byte every 1/5760 seconds (5 per ms, approx.) maximum.
// * Network byte order: multi-byte data is transmitted as big-endian (big end first).
// * 

typedef unsigned char cmd_t;

// -----------------------------------------------------------------------
//
// Incoming commands (RPi -> dsPIC) 
//
// top nibbles
#define CMD_TYPE_LED_OFF        0x0        // bottom 4 bits = LED 1-9
#define CMD_TYPE_LED_ON         0x1        // bottom 4 bits = LED 1-9
#define CMD_TYPE_ALL_LEDS       0x2        // extra byte (leds 1-8, led 9-bit 0 of cmd byte)
// 0x30 unused (ASCII range)
// 0x40 unused (ASCII range)
#define CMD_DISABLE_SERIAL          0x5        // Start of “Uncompressing Linux…”
#define CMD_DISABLE_SERIAL2         0x6        // Start of “Uncompressing Linux…”
// 0x70 unused (ASCII range)
#define CMD_TYPE_POLL           0x8        // bottom 4 bytes ignored / reflected(?) (To be confirmed)
#define CMD_TYPE_REQUEST_STATE  0x9        // nnnn=0 all state (in the following order)
                                            //nnnn=1 LED state
                                            //nnnn=2 movement state
                                            //nnnn=3 IR state
                                            //nnnn=4 battery voltage
                                            //nnnn=5 IR levels
                                            //nnnn=6 move_count
                                            //nnnn=7 reset type
// 0xA0 unused
// 0xB0 unused
#define CMD_TYPE_MOVE_COMMANDS  0xC
#define CMD_TYPE_IR_CONTROL     0xD        // bit 0=1, turn on IR timers, bit 0=0, turn off IR timers.
// 0xE0 unused
#define CMD_TYPE_SYS_REQUESTS   0xF


//
// individual commands
//


#define CMD_POLL            0x80

//#define CMD_ASCII_UNLOCK    '+'            // +++ is unlock
#define CMD_BINARY_UNLOCK1  0xFE         // unlock sequence is 1231. How to ensure not in sequence? Send poll command first. 
#define CMD_BINARY_UNLOCK2  0xFC
#define CMD_BINARY_UNLOCK3  0xF8


// -----------------------------------------------------------------------
//
// Outgoing events (dsPIC -> RPi)
//

// top nibbles
//#define EV_TYPE_BUTTON      0x00
//#define EV_TYPE_            0x10

//#define EV_OLD_EVENT        0x80


//
// individual commands
//
// Reset_Event  0b 0000 0nnn    nnn = reset type
#define EV_UNKNOWN_RESET		0x00
#define EV_POWER_ON_RESET		0x01
#define EV_BROWN_OUT_RESET		0x02
#define EV_WATCHDOG_RESET		0x03
#define EV_SOFTWARE_RESET		0x04
#define EV_EXTERNAL_RESET		0x05
#define EV_EXCEPTION_RESET		0x06

#define EV_BATTERY_VOLTAGE      0x10        // bit 0 and bit 1 plus extra byte
#define EV_FINISHED_MOVE        0x20        // single command

#define EV_BUTTON_A_RELEASE     0x30
#define EV_BUTTON_B_RELEASE     0x31
#define EV_BUTTON_A_PRESS       0x38
#define EV_BUTTON_B_PRESS       0x39


// unlocking
#define EV_UNLOCK_FROM_LOCK     0xC0
#define EV_UNLOCK_FROM_UNLOCK   0xC1
#define EV_LOCK_BY_TIMER        0xC2
#define EV_LOCK_BY_COMMAND      0xC3

#define EV_POLL_REPLY           0x80

// general command / system message 0xEx
#define EV_FAIL_INVALID_COMMAND 0xE2
#define EV_GOT_INSTRUCTION      0xEF



#ifdef	__cplusplus
}
#endif

#endif	/* COMMANDS_REF_H */

