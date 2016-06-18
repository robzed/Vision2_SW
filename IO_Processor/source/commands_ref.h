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
#define CMD_TYPE_REQUEST_STATE  0x9        // nnnn=0 all state <not implemented>(in the following order)
                                            //nnnn=1 LED state <not implemented>
                                            //nnnn=2 movement state<not implemented>
                                            //nnnn=3 <spare>
                                            //nnnn=4 battery voltage <not implemented>
                                            //nnnn=5 <spare>
                                            //nnnn=6 move_count
                                            //nnnn=7 reset type
                                            //nnnn=8 IR front/side state
                                            //nnnn=9 IR 45 state
                                            //nnnn=10 IR front level
                                            //nnnn=11 L90 level
                                            //nnnn=12 L45 level
                                            //nnnn=13 R90 level
                                            //nnnn=14 R45 level

// 0xA0 unused
// 0xB0 unused
#define CMD_TYPE_MOVE_COMMANDS  0xC     // nnnn = 0 stop motors. Also resets wall lock.
                                        // nnnn = 1 forward + 2 bytes distance. Also resets wall lock.
                                        // nnnn = 2 right + 2 bytes distance
                                        // nnnn = 3 left + 2 bytes distance
                                        // nnnn = 4 set speed + 2 bytes distance
                                        // nnnn = 5 set steering correction + 2 bytes distance
                                        // nnnn = 6 extend movement
                                        // nnnn = 7 set cell distance + 2 bytes distance
                                        // nnnn = 8 wall edge correction + 2 bytes distance
                                        // nnnn = 9 set distance to test + 2 bytes distance

#define CMD_TYPE_IR_CONTROL     0xD     // bits 1-3=0, bit 0=1, turn on IR timers, bit 0=0, turn off IR timers.
                                        // bits 0-3 =  8 set_front_long_threshold (+2 bytes)
                                        // bits 0-3 =  9 set_front_short_threshold (+2 bytes)
                                        // bits 0-3 = 10 set_left_side_threshold (+2 bytes)
                                        // bits 0-3 = 11 set_right_side_threshold (+2 bytes)
                                        // bits 0-3 = 12 set_left_45_threshold (+2 bytes)
                                        // bits 0-3 = 13 set_right_45_threshold (+2 bytes)
                                        // bits 0-3 = 14 set_left_45_too_close_threshold (+2 bytes)
                                        // bits 0-3 = 15 set_right_45_too_close_threshold (+2 bytes)
                                           
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
//0x11, 0x12, 0x13 also used.

#define EV_FINISHED_MOVE        0x20        // single command
#define EV_TEST_DISTANCE        0x21        // single command (but always followed immediately by EV_IR_FRONT_SIDE_STATE)

#define EV_SPEED_SAMPLE	0x22		// periodic sample of the speed ... 2 bytes follow
// Also 0x23, 0x24, 0x25 used.
// Decode:
//   left = bit0 cmd as bit8 + byte 1
//  right = bit1 cmd as bit8 + byte 2


#define EV_BUTTON_A_RELEASE     0x30
#define EV_BUTTON_B_RELEASE     0x31
#define EV_BUTTON_A_PRESS       0x38
#define EV_BUTTON_B_PRESS       0x39

#define EV_IR_FRONT_SIDE_STATE  0x40        // bit 0 = front long
                                            // bit 1 = front short
                                            // bit 2 = left side
                                            // bit 3 = right side
#define EV_IR_45_STATE          0x50        // bit 0 = left 45
                                            // bit 1 = right 45
                                            // bit 2 = left 45 too close
                                            // bit 3 = right 45 too close
#define EV_IR_FRONT_LEVEL       0x61
#define EV_L90_LEVEL            0x62
#define EV_L45_LEVEL            0x63
#define EV_R90_LEVEL            0x64
#define EV_R45_LEVEL            0x65


#define EV_STEERING_TRIM_REPORT	0x70		// large_right:8,large_left:4, right:2, left:1
// 0x70 to 0x7F used

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

