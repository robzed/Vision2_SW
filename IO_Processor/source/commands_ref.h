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
//

typedef unsigned char cmd_t;

//
// Incoming commands (RPi -> dsPIC) 
//


#define CMD_ASCII_UNLOCK '+'            // +++ is unlock
#define CMD_BINARY_UNLOCK1 0xFE         // unlock sequence is 1231. How to ensure not in sequence? Send poll command first. 
#define CMD_BINARY_UNLOCK2 0xFC
#define CMD_BINARY_UNLOCK3 0xF8

  
//
// Outgoing events (dsPIC -> RPi)
//

// Reset_Event  0b 0000 0nnn    nnn = reset type
#define EV_UNKNOWN_RESET		0x00
#define EV_POWER_ON_RESET		0x01
#define EV_BROWN_OUT_RESET		0x02
#define EV_WATCHDOG_RESET		0x03
#define EV_SOFTWARE_RESET		0x04
#define EV_EXTERNAL_RESET		0x05
#define EV_EXCEPTION_RESET		0x06

// unlocking
#define EV_UNLOCK_FROM_LOCK     0xC0
#define EV_UNLOCK_FROM_UNLOCK   0xC1
#define EV_LOCK_BY_TIMER        0xC2
#define EV_LOCK_BY_COMMAND      0xC3


#ifdef	__cplusplus
}
#endif

#endif	/* COMMANDS_REF_H */

