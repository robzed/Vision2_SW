/* 
 * File:   main.c
 * Author: Rob Probin
 *
 * Created on 27 June 2014, 20:04
 *
 * Copyright 2014 Rob Probin
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
 */

#include <p30F4011.h>
#include <stdint.h>
#include <stdbool.h>
//#include <stdio.h>
//#include <stdlib.h>

#include "hardware.h"
#include "commands_ref.h"
#include "timer_interrupts.h"

void LED_Test(void)
{
    // LED test
    int led = 1;
    while(1)
    {
        AllLedsOff();
        LedSwitch(led, on);
        if(Grey_A_ButtonPressed())
        {
            led ++;
            if(led > 9)
            {
                led = 1;
            }
        }
        if(Blue_B_ButtonPressed())
        {
            break;
        }
        volatile long int t;
        for(t=0;t<100000;t++)
        {
            // nop
        }
    }
}

void Tests_Finished()
{
    // LED test
    int led = 1;
    int dir = 1;
    while(1)
    {
        AllLedsOff();
        LedSwitch(led, on);

        led += dir;
        if(led > 6 || led < 1)
        {
            dir = -dir;
            led += dir;
        }

        volatile long int t;
        for(t=0;t<50000;t++)
        {
            // nop
        }
    }
}

void FlashAllLEDS(int times)
{
    int i;
    for(i=0; i < times; i++)
    {
        volatile long int t;
        for(t=0;t<100000;t++)
        {
            // nop
        }

        led1=led2=led3=led4=led5=led6=led_front=led_left=led_right=on;

        for(t=0;t<100000;t++)
        {
            // nop
        }

        AllLedsOff();
    }
}

#define SelectButtonA_Grey true
#define SelectButtonB_Blue false

bool button_pressed(bool buttonA)
{
    return buttonA ? Grey_A_ButtonPressed() : Blue_B_ButtonPressed();
}

// Figures just for hardware test
// Not used by Robot maze normally
#define test_front_long_threshold    15
#define test_front_short_threshold   50
#define test_ls_threshold            200
#define test_rs_threshold            200
#define test_r45_threshold           360
#define test_l45_threshold           360
#define test_r45_toclose             540
#define test_l45_toclose             540

void IR_Test(bool button)
{
    int flash = 1;
    while( ! button_pressed(button))
    {
        read_sensor(front);
	read_sensor(side);
        read_sensor(diag);

        AllLedsOff();
        if(front_sensor > test_front_long_threshold && flash)
        {
            led_front = on;
        }
        if(front_sensor > test_front_short_threshold)
        {
            led_front = on;
        }
	if(left_side_sensor > test_ls_threshold)
        {
            led4 = on;
            led5 = on;
            led6 = on;
        }
        if(right_side_sensor > test_rs_threshold)
        {
            led1 = on;
            led2 = on;
            led3 = on;
        }
        if(l45_sensor > test_l45_threshold && flash)
        {
            led_left = on;
        }
        if(l45_sensor > test_l45_toclose)
        {
            led_left = on;
        }
        if(r45_sensor > test_r45_threshold && flash)
        {
            led_right = on;
        }
        if(r45_sensor > test_r45_toclose)
        {
            led_right = on;
        }

        flash = 1-flash;
        delay_ms(10);
    }
}

void BatterySenseTest(bool button)
{
    while( ! button_pressed(button))
    {
        unsigned long battery_volts = adc_read(bat);
        battery_volts *= 5*45*1000L; // 5 volts * 45Kohms * 1000 into millivolts
        battery_volts /= (12*1024); // 12 Kohms and 1024 steps

        // read 0x352 = 850
        // resistors potential divider resistors = 33K / 12K
        // ((850/1024)*5v) * 33K+12K / 12K
        //  = 15.56v  (3.89v per cell)
        // Assuming resistors, 5v, etc. are all correct.
        //
        // limit 0x285 = 645
        // 11.81v (2.95v per cell) ... way too low
        AllLedsOff();
        if(battery_volts < 15000 )
        {
            led1 = on;
        }
        else if(battery_volts < 15500 )
        {
            led2 = on;
        }
        else if(battery_volts < 16000 )
        {
            led3 = on;
        }
        else if(battery_volts < 16500 )
        {
            led4 = on;
        }
        else
        {
            led5 = on;
        }
        led6 = on;

    }
}

void MotorTest(int type, int motor, bool button_A) {
    AllLedsOff();
    if(type == 0)
    {
        led1 = on;
        fwd();
    }
    else if(type == 1)
    {
        led2 = on;
        rev();
    }
    else if(type == 2)
    {
        led1 = on;
        led2 = on;
        turnl();
    }
    else if(type == 3)
    {
        led3 = on;
        turnr();
    }
    en_mot = mot_on;
    while (1)
    {
        if ((button_A && Grey_A_ButtonPressed()) ||
                (!button_A && Blue_B_ButtonPressed()))
        {
            break;
        }
        if(motor == 1)
        {
            led4 = on;
            clk_l = 1;
            delay_ms(5);
            clk_l = 0;
            delay_ms(5);
        }
        else if(motor == 2)
        {
            led5 = on;
            clk_r = 1;
            delay_ms(5);
            clk_r = 0;
            delay_ms(5);
        }
        else if(motor == 3)
        {
            led4 = on;
            led5 = on;
            clk_r = 1;
            clk_l = 1;
            delay_ms(5);
            clk_r = 0;
            clk_l = 0;
            delay_ms(5);
        }
    }
    en_mot = mot_off;
}

#define Motor1FWDTest(_button_A) MotorTest(0, 1, _button_A)
#define Motor1BWDTest(_button_A) MotorTest(1, 1, _button_A)
#define Motor2FWDTest(_button_A) MotorTest(0, 2, _button_A)
#define Motor2BWDTest(_button_A) MotorTest(1, 2, _button_A)
#define MotorBothFWDTest(_button_A) MotorTest(0, 3, _button_A)
#define MotorBothBWDTest(_button_A) MotorTest(1, 3, _button_A)
#define MotorBothTurnLeftTest(_button_A) MotorTest(2, 3, _button_A)
#define MotorBothTurnRightTest(_button_A) MotorTest(3, 3, _button_A)


void SerialInOutTest(bool button)
{
    serial_write_string("\n\nUART test\nWill echo typing\n");
    serial_flush();

    while(!button_pressed(button))
    {
        if(serial_byte_waiting())
        {
            serial_write_char(serial_get_char());
            serial_flush();
        }
    }
}

cmd_t resetSource(void)
{
    if (EXTR)
    {
        return EV_EXTERNAL_RESET;
    }
    if (POR)
    {
        return EV_POWER_ON_RESET;
    }
    if (BOR)
    {
        return EV_BROWN_OUT_RESET;
    }
    if (WDTO)
    {
        return EV_WATCHDOG_RESET;
    }
    if (SWR)
    {
        return EV_SOFTWARE_RESET;
    }
    if (IOPUWR)
    {
        return EV_EXCEPTION_RESET;
    }
    return EV_UNKNOWN_RESET;
}


/*
 * Function for testing hardware
 */
void test_main()
{       
        LED_Test();     // A = step led, B = next test

        FlashAllLEDS(1);
        IR_Test(SelectButtonA_Grey);

        FlashAllLEDS(2);
        BatterySenseTest(SelectButtonB_Blue);

        FlashAllLEDS(4);
        Motor1FWDTest(SelectButtonA_Grey);
        Motor1BWDTest(SelectButtonB_Blue);
        Motor2FWDTest(SelectButtonA_Grey);
        Motor2BWDTest(SelectButtonB_Blue);
        MotorBothFWDTest(SelectButtonA_Grey);
        MotorBothBWDTest(SelectButtonB_Blue);
        MotorBothTurnLeftTest(SelectButtonA_Grey);
        MotorBothTurnRightTest(SelectButtonB_Blue);

        FlashAllLEDS(1);
        SerialInOutTest(SelectButtonA_Grey);

        Tests_Finished();
}


static cmd_t stored_reset_type = EV_UNKNOWN_RESET;

#define COMMANDS_LOCKED 0
#define COMMANDS_BINARY 1
//#define COMMANDS_ASCII 2
static char command_mode = COMMANDS_LOCKED;

/*
char hex_out_table[] = { '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F' };

void send_event_ascii(cmd_t c)
{
    serial_write_char(hex_out_table[c>>4]);
    serial_write_char(hex_out_table[c & 0x0F]);
    serial_write_char(' ');
}

void (*send_event)(cmd_t c) = serial_write_uint8;

void change_send_event()
{
    if(command_mode == COMMANDS_ASCII)
    {
        send_event = send_event_ascii;
    }
    else
    {
        send_event = serial_write_uint8;
    }
}
*/
#define send_event serial_write_uint8

/* 
 * Movement control:
 * 
 *  dist_to_test and dist_test_flag
 * 
 * 	old_left_wall=0;
 *	old_right_wall=0;
 * 
 *  is_timer_finished_move() ... if running
 * 
 */


// event data copies to avoid duplicate events being sent
static unsigned int last_sent_battery = 0;
#define BATTERY_TRANSMIT_ANYWAY_COUNT 20
static int battery_count = BATTERY_TRANSMIT_ANYWAY_COUNT;
static unsigned int set_speed = 50;
static int set_corrector = 10;
bool timer_running = false;
bool ticks_per_motor_enabled = false;
bool trim_report_enabled = false;
bool speed_sample_report_enabled = false;

/*
 * This is the main program for the IO_Processor, which in the case of 
 * Vision2 is a dsPIC30F4011. 
 * 
 * The IO_Processor is responsible for communicating with the IO and doing
 * real-time control. In this case 'real-time' certainly means responding to
 * all events under 1 ms, but also probably under 10ms. Events above 100ms
 * can be handled by the Controller processor, which in the case of Vision2 is
 * a Raspberry Pi model A+. Timings between these two is to be decided.
 */
int main(int argc, char** argv)
{
    ConfigureOscillator();
    InitPorts();
    InitPeripherals();
    
    command_mode = COMMANDS_LOCKED;
    stored_reset_type = resetSource();
    send_event(stored_reset_type);
    timer_running = false;
    
    if(stored_reset_type == EV_POWER_ON_RESET)
    {
        FlashAllLEDS(5);
    }
    else
    {
        FlashAllLEDS(2);
    }

    if(button_pressed(SelectButtonA_Grey))
    {
       test_main();
    }
    
    // we only do this AFTER we've not called test
    init_timer_subsystems();

    
    while(1)
    {
        cmd_t cmd;
        int i;
        
        if(command_mode == COMMANDS_LOCKED)
        {
            cmd_t cmd = serial_get_byte();
            if(cmd == CMD_BINARY_UNLOCK1)
            {
                if(serial_get_byte() != CMD_BINARY_UNLOCK2) { break; }
                if(serial_get_byte() != CMD_BINARY_UNLOCK3) { break; }
                if(serial_get_byte() != CMD_BINARY_UNLOCK1) { break; }
                command_mode = COMMANDS_BINARY;
                //change_send_event();
                send_event(EV_UNLOCK_FROM_LOCK);
                send_event(EV_GOT_INSTRUCTION);     // we need to tell RPi about this command as well.
            }/*
            else if(cmd == CMD_ASCII_UNLOCK)
            {
                if(serial_get_byte() != CMD_ASCII_UNLOCK) { break; }
                if(serial_get_byte() != CMD_ASCII_UNLOCK) { break; }
                command_mode = COMMANDS_ASCII;
                change_send_event();
                send_event(EV_UNLOCK_FROM_LOCK);
            }*/
            // ignore others
        }
        else
        {
            while(command_mode)
            {
                // -----------------------------------------------------
                //
                // check for events
                //
                if(battery_data_ready)
                {
                    // slight race condition here, but not a major problem if we miss one
                    int battery_v = battery_voltage & 0x3FF;
                    battery_data_ready = 0;     // clear request
                    if(battery_v != last_sent_battery || battery_count <= 0)
                    {
                        last_sent_battery = battery_v;
                        send_event(EV_BATTERY_VOLTAGE + (battery_v >> 8));
                        send_event(battery_v & 0xFF);
                        battery_count = BATTERY_TRANSMIT_ANYWAY_COUNT;
                    }
                    else
                    {
                        // We only ignore the reading because it's
                        // the same, but we transmit it every 10 anyway.
                        battery_count --;
                    }
                }
                if(timer_running)
                {
                    if(!is_timer_still_moving())
                    {
                        send_event(EV_FINISHED_MOVE);
                        timer_running = false;
                        
                        if(ticks_per_motor_enabled)
                        {
                            send_event(EV_TICKS_PER_MOTOR);
                            serial_write_int16((ticks_left > 0xFFFF)?0xFFFF:ticks_left);
                            serial_write_int16((ticks_right > 0xFFFF)?0xFFFF:ticks_right);
                            ticks_left = 0;
                            ticks_right = 0;
                        }
                    }
                    else
                    {
                        // some reports are only sent when we are moving
                        if(speed_sample_report_enabled && speed_sample_report)
                        {
                            int left = left_speed_sample;
                            int right = right_speed_sample;
                            speed_sample_report = 0;

                            char ev_code = EV_SPEED_SAMPLE + ((left>256) ? 1 : 0) + ((right>256) ? 2 : 0);

                            send_event(ev_code);
                            send_event(left & 0xFF);
                            send_event(right & 0xFF);
                        }

                        if(trim_report_enabled && trim_report)
                        {
                            send_event(EV_STEERING_TRIM_REPORT + trim_report);
                            trim_report = 0;
                        }
                    }
                }
                
                if(key_A_changed)
                {
                    char key = key_A_stored;
                    key_A_changed = 0;
                    send_event(key?EV_BUTTON_A_PRESS:EV_BUTTON_A_RELEASE);
                }
                if(key_B_changed)
                {
                    char key = key_B_stored;
                    key_B_changed = 0;
                    send_event(key?EV_BUTTON_B_PRESS:EV_BUTTON_B_RELEASE);
                }
                
                if(get_distance_test_flag())
                {
                    send_event(EV_TEST_DISTANCE);
                    send_event(EV_IR_FRONT_SIDE_STATE + get_ir_front_side_bitmap());
                }
                
                // -----------------------------------------------------
                //
                // process commands
                //
                if(serial_byte_waiting())
                {
                    cmd = serial_get_byte();
                    //if(command_mode == COMMANDS_ASCII)
                    //{
                    //    
                    //}
                    cmd_t low_nibble = cmd&0x0F;
                    switch(cmd >> 4)
                    {
                        case CMD_TYPE_LED_OFF:
                            LedSwitch(low_nibble, off);
                            break;
                        case CMD_TYPE_LED_ON:
                            LedSwitch(low_nibble, on);
                            break;
                        case CMD_TYPE_ALL_LEDS:
                            LedSwitch(9, low_nibble&0x01);
                            cmd = serial_get_byte();
                            for(i = 1; i < 9; i++)
                            {
                                LedSwitch(i, cmd&0x01);
                                cmd >>= 1;
                            }
                            break;
                        case CMD_DISABLE_SERIAL:
                            // any lower nibble
                            send_event(EV_LOCK_BY_COMMAND);
                            break;
                        case CMD_DISABLE_SERIAL2:
                            // any lower nibble
                            send_event(EV_LOCK_BY_COMMAND);
                            break;                    
                        case CMD_TYPE_POLL:
                            send_event(EV_POLL_REPLY + low_nibble);
                            break;
                        case CMD_TYPE_REQUEST_STATE:
                            switch(low_nibble)
                            {
                                case 4: // battery voltage
                                {
                                    int battery_v = battery_voltage & 0x3FF;
                                    send_event(EV_BATTERY_VOLTAGE + (battery_v >> 8));
                                    send_event(battery_v & 0xFF);
                                    break;
                                }
                                case 8: //IR front/side state
                                    send_event(EV_IR_FRONT_SIDE_STATE + get_ir_front_side_bitmap());
                                    break;
                                case 9: //IR 45 state
                                    send_event(EV_IR_45_STATE + get_ir_45_bitmap());
                                    break;
                                case 10: // IR front level
                                    send_event(EV_IR_FRONT_LEVEL);
                                    serial_write_int16(front_sensor);
                                    break;
                                case 11: // L90 level
                                    send_event(EV_L90_LEVEL);
                                    serial_write_int16(left_side_sensor);
                                    break;
                                case 12: // L45 level
                                    send_event(EV_L45_LEVEL);
                                    serial_write_int16(l45_sensor);
                                    break;
                                case 13: // R90 level
                                    send_event(EV_R90_LEVEL);
                                    serial_write_int16(right_side_sensor);
                                    break;
                                case 14: // R45 level
                                    send_event(EV_R45_LEVEL);
                                    serial_write_int16(r45_sensor);
                                    break;
                                default:
                                    send_event(EV_FAIL_INVALID_COMMAND);
                                    break;
                            }
                            break;
                        case CMD_TYPE_MOVE_COMMANDS:
                            switch(low_nibble)
                            {
                                case 0: // motors off
                                    en_mot = mot_off;
                                    reset_wall_edge_flag();
                                    break;
                                case 1: // forward (parameter = distance)
                                    en_mot = mot_on;
                                    reset_wall_edge_flag();
                                    fwd();
                                    timer_move(serial_get_int16(), set_speed, set_corrector);
                                    timer_running = true;
                                    // make sure we don't get stale data
                                    trim_report = 0;
                                    speed_sample_report = 0;
                                    break;
                                    
                                case 2: // right (parameter = distance)
                                    en_mot = mot_on;
                                    turnr();
                                    timer_move(serial_get_int16(), set_speed, set_corrector);
                                    timer_running = true;
                                    // make sure we don't get stale data
                                    trim_report = 0;
                                    speed_sample_report = 0;
                                    break;
                                case 3: // left (parameter = distance)
                                    en_mot = mot_on;
                                    turnl();
                                    timer_move(serial_get_int16(), set_speed, set_corrector);
                                    timer_running = true;
                                    // make sure we don't get stale data
                                    trim_report = 0;
                                    speed_sample_report = 0;
                                    break;
                                case 4: // set speed
                                    set_speed = serial_get_uint16();
                                    break;
                                case 5: // set steering correction
                                    set_corrector = serial_get_int16();
                                    break;
                                case 6: // extend movement
                                    timer_fine_to_move_another_cell();
                                    break;
                                case 7: // set cell distance (+2 bytes)
                                    set_cell_distance(serial_get_int16());
                                    break;
                                case 8: // set correction distance (+2 bytes)
                                    set_wall_edge_to_crt_distance(serial_get_int16());
                                    break;
                                case 9: // set distance to test (+2 bytes)
                                    set_distance_to_test(serial_get_int16());
                                    break;
                                    
                                case 0x0F:
                                    cmd = serial_get_byte();
                                    send_event(EV_CONFIG_PARAMETER_VALUE);
                                    switch(cmd)
                                    {
                                    case 0xC5: // set steering correction   
                                        serial_write_int16(set_corrector);
                                        break;
                                    case 0xC7: // set cell distance (+2 bytes)
                                        serial_write_int16(get_cell_distance());
                                        break;
                                    case 0xC8: // set correction distance (+2 bytes)
                                        serial_write_int16(get_wall_edge_to_crt_distance());
                                        break;
                                    case 0xC9: // set distance to test (+2 bytes)
                                        serial_write_int16(get_distance_to_test());
                                        break;
                                    default:
                                        break;
                                    }
                                    break;
                                    
                                default:
                                    break;
                            }
                            break;
                        case CMD_TYPE_IR_CONTROL:
                            switch(low_nibble)
                            {
                                case 0:
                                    disable_IR_scanning();
                                    break;
                                case 1:
                                    enable_IR_scanning();
                                    break;

                                case 8:
                                    set_front_long_threshold(serial_get_int16());
                                    break;
                                case 9:
                                    set_front_short_threshold(serial_get_int16());
                                    break;
                                case 10:
                                    set_left_side_threshold(serial_get_int16());
                                    break;
                                case 11:
                                    set_right_side_threshold(serial_get_int16());
                                    break;
                                case 12:
                                    set_left_45_threshold(serial_get_int16());
                                    break;
                                case 13:
                                    set_right_45_threshold(serial_get_int16());
                                    break;
                                case 14:
                                    set_left_45_too_close_threshold(serial_get_int16());
                                    break;
                                case 15:
                                    set_right_45_too_close_threshold(serial_get_int16());
                                    break;
                                default:
                                    break;
                            }
                            break;
                        case CMD_TYPE_SYS_REQUESTS: 
                            if(cmd == CMD_WRITE_TO_ACCEL0)
                            {
                                int addr = serial_get_byte();
                                write_acceleration_value(addr, serial_get_int16());
                                send_event(EV_VALUE_FOR_ACCEL);
                                serial_write_int16(get_acceleration_value(addr));
                                break;
                            }
                            else if(cmd == CMD_WRITE_TO_ACCEL1)
                            {
                                int addr = serial_get_byte()+256;
                                write_acceleration_value(addr, serial_get_int16());
                                send_event(EV_VALUE_FOR_ACCEL);
                                serial_write_int16(get_acceleration_value(addr));
                                break;
                            }
                            else if(cmd == CMD_SWITCH_OPTIONS)
                            {
                                ticks_per_motor_enabled = false;
                            }
                            else if(cmd == CMD_SWITCH_OPTIONS+1)
                            {
                                ticks_per_motor_enabled = true;
                            }
                            else if(cmd == CMD_SWITCH_OPTIONS+2)
                            {
                                trim_report_enabled = false;
                            }
                            else if(cmd == CMD_SWITCH_OPTIONS+3)
                            {
                                trim_report_enabled = true;
                            }
                            else if(cmd == CMD_SWITCH_OPTIONS+4)
                            {
                                speed_sample_report_enabled = false;
                            }
                            else if(cmd == CMD_SWITCH_OPTIONS+5)
                            {
                                speed_sample_report_enabled = true;
                            }
                            else
                            {
                                // for the moment, assume all unlock requests
                                send_event(EV_UNLOCK_FROM_UNLOCK);
                            }
                            break;
                        default:
                            send_event(EV_FAIL_INVALID_COMMAND);
                            break;
                            
                    } // switch on upper nibble
                    
                    // finally, when read all bytes ... tell the host we are OK
                    send_event(EV_GOT_INSTRUCTION);
                }   // if byte waiting
                
            } // while(command_mode)
        } // else (not locked)
    } // while(1)
    return 0;
}

