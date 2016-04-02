/* 
 * File:   main.c
 * Author: Rob Probin
 *
 * Created on 27 June 2014, 20:04
 */

#include <p30F4011.h>
#include <stdint.h>
#include <stdbool.h>
//#include <stdio.h>
//#include <stdlib.h>

#include "hardware.h"

void LED_Test(void)
{
    // LED test
    int led = 1;
    while(1)
    {
        AllLedsOff();
        LedOn(led);
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
        LedOn(led);

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


// figures just for test
#define front_long_threshold    15
#define front_short_threshold   50
#define ls_threshold            200
#define rs_threshold            200
#define r45_threshold           360
#define l45_threshold           360
#define r45_toclose             540
#define l45_toclose             540

extern unsigned int front_sensor;
extern unsigned int right_side_sensor;
extern unsigned int left_side_sensor;
extern unsigned int r45_sensor;
extern unsigned int l45_sensor;

void IR_Test(bool button)
{
    int flash = 1;
    while( ! button_pressed(button))
    {
        read_sensor(front);
	read_sensor(side);
        read_sensor(diag);

        AllLedsOff();
        if(front_sensor > front_long_threshold && flash)
        {
            led_front = on;
        }
        if(front_sensor > front_short_threshold)
        {
            led_front = on;
        }
	if(left_side_sensor > ls_threshold)
        {
            led4 = on;
            led5 = on;
            led6 = on;
        }
        if(right_side_sensor > rs_threshold)
        {
            led1 = on;
            led2 = on;
            led3 = on;
        }
        if(l45_sensor > l45_threshold && flash)
        {
            led_left = on;
        }
        if(l45_sensor > l45_toclose)
        {
            led_left = on;
        }
        if(r45_sensor > r45_threshold && flash)
        {
            led_right = on;
        }
        if(r45_sensor > r45_toclose)
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

/*
 * This is the main program for the IO_Processor, which in the case of 
 * Vision2 is a dsPIC30F4011. 
 * 
 * The IO_Processor is responsible for communicating with the IO and doing
 * real-time control. In this case 'real-time' certainly means responding to
 * all events under 1 ms, but also probably under 10ms. Events above 100ms
 * can be handled by the Controller processor, which in the case of Vision2 is
 * a Raspberry Pi model A. Timings between these two is to be decided.
 */
int main(int argc, char** argv)
{
    ConfigureOscillator();
    InitPorts();
    InitPeripherals();

    while(1)
    {
        FlashAllLEDS(5);
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
    //return (EXIT_SUCCESS);
}

