/*
 * File:   hardware.c
 * Author: rob
 *
 * Created on 27 June 2014, 21:29
 * 
 * Init routines like Ratty2 V-r100.c by Barry Grub 30/12/2009
 */

#include "hardware.h"


void ConfigureOscillator(void)
{
    // nothing to do here
}

void InitPorts(void)
{
    // Configure I/O port directions
    TRISB=0x003F;
    // configure Port B, Bits 0 to 5 as analogue
    ADPCFG=0xFFC0;
    TRISC=0xC000;
    TRISD=0;
    TRISE=0x0104;
    TRISF=0x000C;

    AllLedsOff();
    // motors off before we start
    en_mot=mot_off;
}

void init_adc(void)
{
    ADCON1bits.ADON = 0;  // disable the ADC
    ADCON1bits.FORM = 0;  // don't sign extended output
    ADCON1bits.SSRC = 0;  // Clearing SAMP bit ends sampling and starts conversion
    ADCON1bits.ASAM = 0;  // sampling begins when SAMP is set
    ADCSSL=0;
    ADCON3bits.ADCS = 3;
    ADCON1bits.ADON = 1;  // enable the ADC
}

void init_uart(void)
{
	U1BRG=8;					//set baud rate 57600
	U1MODE=0x8400;			//enable UART, select Alt pins
							//8 data bits 1 stop bit
	U1STA=0x8400;				//Enable interrupt, enable Transmit
}

void InitPeripherals(void)
{
    init_adc();
    init_uart();
}


void LedSwitch(int led, int state)
{
    //irled_90 = off;      // hack test
    //irled_45 = off;      // hack test
    //irled_front = off;      // hack test
    if(led > 6)
    {
        if(led == 7)
        {
            //irled_90 = on;      // hack test
            led_left = on;
        }
        else if(led == 8)
        {
            //irled_45 = on;      // hack test
            led_right = on;
        }
        else
        {
            //irled_front = on;      // hack test
            led_front = on;
        }
    }
    else if(led > 3)
    {
        if(led == 4)
        {
            led4 = on;
        }
        else if(led == 5)
        {
            led5 = on;
        }
        else
        {
            led6 = on;
        }
    }
    else
    {
        if(led == 1)
        {
            led1 = on;
        }
        else if(led == 2)
        {
            led2 = on;
        }
        else
        {
            led3 = on;
        }
    }
}
void AllLedsOff(void)
{
    led1=led2=led3=led4=led5=led6=led_front=led_left=led_right=off;
}


static volatile int temp_count = 0;

// taken from Barry Grubb's code
void delay_us( unsigned int us_count )
{
    temp_count = us_count +1;
    asm volatile("outer1: dec _temp_count");
    asm volatile("cp0 _temp_count");
    asm volatile("bra z, done1");
    asm volatile("nop");
    asm volatile("nop");
    asm volatile("nop");
    asm volatile("nop");
    asm volatile("nop");
    asm volatile("nop");
    asm volatile("nop");
    asm volatile("nop");
    asm volatile("nop");
    asm volatile("nop");
    asm volatile("nop");
    asm volatile("bra outer1");
    asm volatile("done1:");
}


void delay_ms(unsigned int ms_count)
{
    int i;
    for(i = 0; i < ms_count; i++)
    {
        delay_us(1000);
    }
}

// sensors when on
unsigned int front_sensor=0;
unsigned int right_side_sensor=0;
unsigned int left_side_sensor=0;
unsigned int r45_sensor=0;
unsigned int l45_sensor=0;

// sensors when off
static volatile unsigned int front_off=0;
static volatile unsigned int right_off=0;
static volatile unsigned int left_off=0;
static volatile unsigned int r45_off=0;
static volatile unsigned int l45_off=0;

// taken from Barry Grubb's code
unsigned int adc_read(unsigned int chan)
{	ADCHS = chan;
	ADCON1bits.SAMP = 1;			// start sampling
	delay_us(1);
	ADCON1bits.SAMP = 0;			// start Converting
	while (!ADCON1bits.DONE);			// conversion done?
	return ADCBUF0;
}

// taken from Barry Grubb's code
void read_sensor(char sensor) {
    switch (sensor) {
        case front:
            front_off = adc_read(fr);
            irled_front = on; //turn on the front IR emitter
            delay_us(10); //wait for IRled to come on
            front_sensor = adc_read(fr) - front_off; //read the A2D
            irled_front = off;
            break;
        case side:
            right_off = adc_read(r90);
            left_off = adc_read(l90);
            irled_90 = on;
            delay_us(10);
            right_side_sensor = adc_read(r90) - right_off;
            left_side_sensor = adc_read(l90) - left_off;
            irled_90 = off;
            break;
        case diag:
            r45_off = adc_read(r45);
            l45_off = adc_read(l45);
            irled_45 = on;
            delay_us(10);
            r45_sensor = adc_read(r45) - r45_off;
            l45_sensor = adc_read(l45) - l45_off;
            irled_45 = off;
            break;
        default:
            break;
    }
}

// should be background writes
// 4-word deep transmit data buffer
// 4-word deep receive data buffer
void serial_write_string(char* s)
{
    char c;
    while ( (c = *s) )
    {
        while (U1STAbits.UTXBF == 1)
        { /* nop */ }
        U1TXREG = c;
        s++;
    }
}

void serial_write_data(uint8_t* s, int l)
{
    while (l > 0)
    {
        while (U1STAbits.UTXBF == 1)
        { /* nop */ }
        U1TXREG = *s;
        s++;
        l--;
    }
}

void serial_write_char(char c)
{
    while (U1STAbits.UTXBF == 1)
    { /* nop */ }
    U1TXREG = c;
}

void serial_write_uint8(uint8_t byte)
{
    while (U1STAbits.UTXBF == 1)
    { /* nop */ }
    U1TXREG = byte;
}

// network byte order
void serial_write_int16(int16_t data)
{
    serial_write_uint8(data >> 8);
    serial_write_uint8(data & 0xFF);
}

void serial_flush(void)
{
    // used when buffered
}

bool serial_byte_waiting()
{
    return U1STAbits.URXDA == 1;
}

int serial_get_byte()
{
    if(U1STAbits.OERR == 1)
    {
        U1STAbits.OERR = 0;
    }
    if(U1STAbits.FERR == 1)
    {
    }
    while(U1STAbits.URXDA == 0)
    { /* nop */ }
    return U1RXREG;
}

int serial_get_char()
{
    return (char)serial_get_byte();
}

unsigned int serial_get_uint16(void)
{
    int upper = serial_get_byte();
    return (upper << 8) + serial_get_byte();
}

int serial_get_int16(void)
{
    int upper = serial_get_byte();
    return (upper << 8) + serial_get_byte();
}


volatile unsigned int battery_voltage;
volatile char battery_data_ready = 0;

void battery_check(void)
{
    battery_voltage = adc_read(bat);
    battery_data_ready = 1;
}

#define KEY_DEBOUNCE_COUNT 3

volatile char key_A_stored = 0;
volatile char key_A_changed = 0;
static char key_A_debounce = KEY_DEBOUNCE_COUNT;

volatile char key_B_stored = 0;
volatile char key_B_changed = 0;
static char key_B_debounce = KEY_DEBOUNCE_COUNT;

void key_scan(void)
{
    // we only debounce a new state change if we've read the previous one.
    char key = Grey_A_ButtonPressed();
    if(!key_A_changed && key != key_A_stored)
    {
        key_A_debounce--;
        if(key_A_debounce == 0)
        {
            key_A_stored = key;
            key_A_changed = 1;
            key_A_debounce = KEY_DEBOUNCE_COUNT;
        }
    }
    else
    {
        key_A_debounce = KEY_DEBOUNCE_COUNT;
    }

    key = Blue_B_ButtonPressed();
    if(!key_B_changed && key != key_B_stored)
    {
        key_B_debounce--;
        if(key_B_debounce == 0)
        {
            key_B_stored = key;
            key_B_changed = 1;
            key_B_debounce = KEY_DEBOUNCE_COUNT;
        }
    }
    else
    {
        key_B_debounce = KEY_DEBOUNCE_COUNT;
    }
}

