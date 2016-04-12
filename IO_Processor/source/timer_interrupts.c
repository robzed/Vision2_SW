/* 
 * File:   timer_interrupts.c
 * Author: Rob Probin
 * Mostly copied from V_r100.c, created by Barry Grubb
 *
 * Created on April 10, 2016, 9:45 AM
 */

#include "hardware.h"
#include "timer_interrupts.h"

void sensor_select(void);

static volatile int d_t_g=0;                // distance to go

// these two are special feature to test for walls along a straight (normally))
static volatile int dist_to_test=0;         // distance to test for walls
static volatile int dist_test_flag=0;       // flag that changes state when dist_to_test is reached and every cell afterwards

static volatile unsigned int l_index=0;         // left motor speed level (internal)
static volatile unsigned int r_index=0;         // right motor speed level (internal))
static volatile unsigned int l_speed=50;        // maximum speed left
static volatile unsigned int r_speed=50;        // maximum speed right


// These trim flags communicate steering corrections between 
// IR sensor timer interrupt and motor timer interrupt
static unsigned int left_trim_flag=0;  // adjust left (internal)
static volatile unsigned int right_trim_flag=0; // adjust right (internal)
static volatile unsigned int large_trim_flag=0; // large adjust required (internal)

static unsigned int sensor_count=1;         // the IR sensor read order index (internal)

// these are just used inside sensor_select() to create wall_edge_flag
static volatile int left_wall=0;        // left wall now? (internal)
static volatile int old_left_wall=0;    // previously a left wall? (internal)
static volatile int right_wall=0;       // right wall now? (internal)
static volatile int old_right_wall=0;   // previously a right wall? (internal)

// This is communication between the  IR sensor timer interrupt and motor 
// timer interrupt to resynchronise the centre of a cell based on a passing 
// wall edge. We only do this when we are stopping in this cell.
static volatile int wall_edge_flag=0;       // resynchronise the distance to go (internal)

static volatile int d_t_g_flag=0;       // it's fine to carry on an extra cell

static volatile int corrector=0;        // steering correction factor

//
// internal working 'constants'
//
static int cell	= 347;			//adjust these values for cell distance		


static int wall_edge_to_crt	= 230;	//front error correction value
								//should equal distance from wall edge to
								//centre of square 

static int front_long_threshold = 15;		// is there a wall far away - used for moving ahead on explore
static int front_short_threshold = 50;     // front wall detection (also stops steering problems on turn)
static int ls_threshold = 200;    // side wall detection
static int rs_threshold = 200;    // side wall detection
static int r45_threshold = 540;   // steering
static int l45_threshold = 360;   // steering
static int r45_toclose	= 760;     // gross steering
static int l45_toclose	= 580;     // gross steering


//***************************************************************************************
//acceleration/deacceleration table used for left and right motor
//***************************************************************************************

int acc_table[512] __attribute__((space(auto_psv)))=
{
0x77FC,0x31B3,0x2622,0x2026,0x1C53,0x199B,0x178C,0x15EB,0x1496,0x1378,
0x1284,0x11B1,0x10F8,0x1054,0x0FC1,0x0F3D,0x0EC5,0x0E57,0x0DF3,0x0D96,
0x0D40,0x0CF0,0x0CA5,0x0C60,0x0C1E,0x0BE1,0x0BA7,0x0B70,0x0B3C,0x0B0B,
0x0ADD,0x0AB0,0x0A86,0x0A5D,0x0A36,0x0A11,0x09EE,0x09CC,0x09AB,0x098B,
0x096D,0x0950,0x0933,0x0918,0x08FE,0x08E4,0x08CC,0x08B4,0x089D,0x0886,
0x0871,0x085C,0x0847,0x0833,0x0820,0x080D,0x07FB,0x07E9,0x07D7,0x07C7,
0x07B6,0x07A6,0x0796,0x0787,0x0778,0x0769,0x075B,0x074D,0x073F,0x0732,
0x0725,0x0718,0x070B,0x06FF,0x06F3,0x06E7,0x06DB,0x06D0,0x06C5,0x06BA,
0x06AF,0x06A5,0x069A,0x0690,0x0686,0x067C,0x0673,0x0669,0x0660,0x0657,
0x064E,0x0645,0x063C,0x0634,0x062B,0x0623,0x061B,0x0613,0x060B,0x0603,
0x05FB,0x05F4,0x05EC,0x05E5,0x05DE,0x05D7,0x05D0,0x05C9,0x05C2,0x05BB,
0x05B5,0x05AE,0x05A7,0x05A1,0x059B,0x0595,0x058E,0x0588,0x0582,0x057C,
0x0577,0x0571,0x056B,0x0565,0x0560,0x055A,0x0555,0x0550,0x054A,0x0545,
0x0540,0x053B,0x0536,0x0531,0x052C,0x0527,0x0522,0x051D,0x0519,0x0514,
0x050F,0x050B,0x0506,0x0502,0x04FD,0x04F9,0x04F4,0x04F0,0x04EC,0x04E8,
0x04E3,0x04DF,0x04DB,0x04D7,0x04D3,0x04CF,0x04CB,0x04C7,0x04C3,0x04C0,
0x04BC,0x04B8,0x04B4,0x04B1,0x04AD,0x04A9,0x04A6,0x04A2,0x049F,0x049B,
0x0498,0x0494,0x0491,0x048D,0x048A,0x0487,0x0484,0x0480,0x047D,0x047A,
0x0477,0x0473,0x0470,0x046D,0x046A,0x0467,0x0464,0x0461,0x045E,0x045B,
0x0458,0x0455,0x0452,0x0450,0x044D,0x044A,0x0447,0x0444,0x0442,0x043F,
0x043C,0x0439,0x0437,0x0434,0x0431,0x042F,0x042C,0x042A,0x0427,0x0425,
0x0422,0x0420,0x041D,0x041B,0x0418,0x0416,0x0413,0x0411,0x040E,0x040C,
0x040A,0x0407,0x0405,0x0403,0x0401,0x03FE,0x03FC,0x03FA,0x03F8,0x03F5,
0x03F3,0x03F1,0x03EF,0x03ED,0x03EA,0x03E8,0x03E6,0x03E4,0x03E2,0x03E0,
0x03DE,0x03DC,0x03DA,0x03D8,0x03D6,0x03D4,0x03D2,0x03D0,0x03CE,0x03CC,
0x03CA,0x03C8,0x03C6,0x03C4,0x03C2,0x03C0,0x03BE,0x03BD,0x03BB,0x03B9,
0x03B7,0x03B5,0x03B3,0x03B2,0x03B0,0x03AE,0x03AC,0x03AB,0x03A9,0x03A7,
0x03A5,0x03A4,0x03A2,0x03A0,0x039E,0x039D,0x039B,0x0399,0x0398,0x0396,
0x0395,0x0393,0x0391,0x0390,0x038E,0x038C,0x038B,0x0389,0x0388,0x0386,
0x0385,0x0383,0x0381,0x0380,0x037E,0x037D,0x037B,0x037A,0x0378,0x0377,
0x0375,0x0374,0x0373,0x0371,0x0370,0x036E,0x036D,0x036B,0x036A,0x0368,
0x0367,0x0366,0x0364,0x0363,0x0362,0x0360,0x035F,0x035D,0x035C,0x035B,
0x0359,0x0358,0x0357,0x0355,0x0354,0x0353,0x0351,0x0350,0x034F,0x034E,
0x034C,0x034B,0x034A,0x0348,0x0347,0x0346,0x0345,0x0343,0x0342,0x0341,
0x0340,0x033F,0x033D,0x033C,0x033B,0x033A,0x0339,0x0337,0x0336,0x0335,
0x0334,0x0333,0x0332,0x0330,0x032F,0x032E,0x032D,0x032C,0x032B,0x032A,
0x0328,0x0327,0x0326,0x0325,0x0324,0x0323,0x0322,0x0321,0x0320,0x031E,
0x031D,0x031C,0x031B,0x031A,0x0319,0x0318,0x0317,0x0316,0x0315,0x0314,
0x0313,0x0312,0x0311,0x0310,0x030F,0x030E,0x030D,0x030C,0x030B,0x030A,
0x0309,0x0308,0x0307,0x0306,0x0305,0x0304,0x0303,0x0302,0x0301,0x0300,
0x02FF,0x02FE,0x02FD,0x02FC,0x02FB,0x02FA,0x02F9,0x02F8,0x02F7,0x02F6,
0x02F6,0x02F5,0x02F4,0x02F3,0x02F2,0x02F1,0x02F0,0x02EF,0x02EE,0x02ED,
0x02EC,0x02EC,0x02EB,0x02EA,0x02E9,0x02E8,0x02E7,0x02E6,0x02E5,0x02E5,
0x02E4,0x02E3,0x02E2,0x02E1,0x02E0,0x02DF,0x02DF,0x02DE,0x02DD,0x02DC,
0x02DB,0x02DA,0x02DA,0x02D9,0x02D8,0x02D7,0x02D6,0x02D6,0x02D5,0x02D4,
0x02D3,0x02D2,0x02D1,0x02D1,0x02D0,0x02CF,0x02CE,0x02CE,0x02CD,0x02CC,
0x02CB,0x02CA,0x02CA,0x02C9,0x02C8,0x02C7,0x02C7,0x02C6,0x02C5,0x02C4,
0x02C4,0x02C3,0x02C2,0x02C1,0x02C1,0x02C0,0x02BF,0x02BE,0x02BE,0x02BD,
0x02BC,0x02BB,0x02BB,0x02BA,0x02B9,0x02B9,0x02B8,0x02B7,0x02B6,0x02B6,
0x02B5,0x02B4,0x02B4,0x02B3,0x02B2,0x02B1,0x02B1,0x02B0,0x02AF,0x02AF,
0x02AE,0x02AD,0x02AD,0x02AC,0x02AB,0x02AB,0x02AA,0x02A9,0x02A9,0x02A8,
0x02A7,0x02A7,
};
//*************************************************************************************

// IR sensors, Base clock = 125KHz or 8us, actual expiry = 125000/0x800 = 16.376ms. 
// Notice, out of phase with battery...
void init_timer1(void)
{	T1CON=0;				//stops timer1 and reset control register
	TMR1=0;				//clear contents of timer register
	PR1=0x07FF;			//load timer value into period register
	IPC0bits.T1IP=1;		//set timer1 interrupt priority to 1
	T1CONbits.TCKPS=2;		//set timer1 prescale to 1:64
	IFS0bits.T1IF=1;		//clear timer1 interrupt status flag
	IEC0bits.T1IE=1;		//enable timer1 interrupts
	//to start timer1 - T1CONbits.TON=1
}	

// Left Motor (FCY/8 = 1MHz, therefore 1us*10 = 100,000KHz)
void init_timer2(void)
{	T2CON=0;				//stops timer2 and reset control register
	TMR2=0;				//clear contents of timer register
	PR2=0x000A;			//load timer value into period register
	IPC1bits.T2IP=4;		//set timer2 interrupt priority to 4
	T2CONbits.TCKPS=1;		//set timer2 prescale to 1:8
	IFS0bits.T2IF=1;		//clear timer2 interrupt status flag
	IEC0bits.T2IE=1;		//enable timer2 interrupts
	//to start timer2 - T2CONbits.TON=1
}

// Battery Sensor, Base clock = 125KHz or 8us, actual expiry = 125000/4096 = 32.768ms
void init_timer3(void)
{	T3CON=0;				//stops timer3 and reset control register
	TMR3=0;				//clear contents of timer register
	PR3=0x1000;			//load timer value into period register
	IPC1bits.T3IP=1;		//set timer3 interrupt priority to 1
	T3CONbits.TCKPS=2;		//set timer3 prescale to 1:64
	IFS0bits.T3IF=1;		//clear timer3 interrupt status flag
	IEC0bits.T3IE=1;		//enable timer3 interrupts
	//to start timer3 - T3CONbits.TON=1
}

// Right motor (FCY/8 = 1MHz, therefore 1us*10 = 100,000KHz)
void init_timer4(void)
{	T4CON=0;				//stops timer4 and reset control register
	TMR4=0;				//clear contents of timer register
	PR4=0x000A;			//load timer value into period register
	IPC5bits.T4IP=4;		//set timer4 interrupt priority to 4
	T4CONbits.TCKPS=1;		//set timer4 prescale to 1:8
	IFS1bits.T4IF=1;		//clear timer4 interrupt status flag
	IEC1bits.T4IE=1;		//enable timer4 interrupts
	//to start timer4 - T4CONbits.TON=1
}


//***************************************************************************************************
//sensor read timer interrupt
//***************************************************************************************************
void __attribute__((__interrupt__,auto_psv))_T1Interrupt(void)
{
	IFS0bits.T1IF = 0; 		// clear timer1 interrupt status flag
	sensor_select();
}
//***************************************************************************************************
//battery monitor timer interrupt
//***************************************************************************************************
void __attribute__((__interrupt__,auto_psv))_T3Interrupt(void)
{	
	IFS0bits.T3IF = 0; 		// clear timer3 interrupt status flag
	battery_check();
    key_scan();
}


//**************************************************************************************************
//left motor interrupt
//**************************************************************************************************
void __attribute__((__interrupt__,shadow,auto_psv))_T2Interrupt(void)
{	int x;
	IFS0bits.T2IF = 0;				// clear timer2 interrupt status flag
	
	x=acc_table[l_index];
	if (left_trim_flag)
		{	if(large_trim_flag)
				{x=(x>>1)+(x>>2);}			//reduse time to 0.75
			else
				{x=(x>>1)+(x>>2)+(x>>3);}	//reduce time to 0.875
			left_trim_flag--;
			//led2=on;
		} 
	PR2=x;
	if (d_t_g<l_index) l_index--;			//slow down
	else if (l_index>l_speed) l_index--;
	else if (l_index<l_speed)l_index++;		//speed up
	clk_l=1;
	for(x=0 ; x<10; x++);					//short delay for motor pulse
	clk_l=0;
	d_t_g--;								//decrement distance to go
		if (d_t_g==0)
		{	T2CONbits.TON=0;		//left motor timer stop
			T4CONbits.TON=0;		//right motor timer stop
			l_index=r_index=0;
		}
	if(d_t_g_flag){d_t_g+=cell;d_t_g_flag=0;} //d_t_g_flag = good to go extra cell	
	if(wall_edge_flag&&(d_t_g<cell)){d_t_g=wall_edge_to_crt;
								wall_edge_flag=0;}
										// front error correction
	dist_to_test--;
	if (dist_to_test==0) {dist_test_flag=1; dist_to_test+=cell;}
										//carry on if walls both sides
}
//**************************************************************************************************
//Right motor interrupt
//**************************************************************************************************
void __attribute__((__interrupt__,shadow,auto_psv))_T4Interrupt(void)
{	int x;
	IFS1bits.T4IF = 0;				// clear timer4 interrupt status flag
	x=acc_table[r_index];
	if (right_trim_flag)
		{	if(large_trim_flag)
				{x=(x>>1)+(x>>2);}			//reduse time to 0.75
			else
				{x=(x>>1)+(x>>2)+(x>>3);}	//reduce time to 0.875
			right_trim_flag--;
			//led2=on;
		}
	PR4=x;
	if (d_t_g<r_index) r_index--;
	else if (r_index>r_speed) r_index--;
	else if (r_index<r_speed)r_index++;
	clk_r=1;
	for(x=0 ; x<10; x++);
	clk_r=0;
}
//************************************************************************************************



void sensor_select(void)
{
	sensor_count++;
	if (sensor_count>3)sensor_count=1;
		
	if(sensor_count==1)
		{
			read_sensor(front);
			if (front_sensor>front_long_threshold) led_front=on;
			 else led_front=off;
		}	
	if(sensor_count==2)
		{	read_sensor(diag);
			large_trim_flag=0;
			if(front_sensor<front_short_threshold)	//no steering if close to front wall	
				{
						if (l45_sensor>l45_threshold)
						{	if (l45_sensor>l45_toclose)large_trim_flag=1;
							left_trim_flag=corrector;
							led_left=on;
						}
						else
						{led_left=off;}
	
						if (r45_sensor>r45_threshold)
						{	if (r45_sensor>r45_toclose)large_trim_flag=1;
							right_trim_flag=corrector;
							led_right=on;
						}
						else
						{led_right=off;	}
				}			
		}
	if(sensor_count==3)
		{
			read_sensor(side);	
			if (left_side_sensor>ls_threshold)
				{ left_wall=1;
				 // led_left=on;
				 }
			else
				{ left_wall=0;
				 // led_left=off;
				  }
			if (old_left_wall>left_wall)
				{wall_edge_flag=1;
				}
				  
			if (right_side_sensor>rs_threshold)
				{ right_wall=1;
				 // led_right=on;
				  }
			else
				{ right_wall=0;
				 // led_right=off;
				  }
			if (old_right_wall>right_wall)
				{wall_edge_flag=1;}
			
			old_left_wall=left_wall;
			old_right_wall=right_wall;
		}
		
}	


void init_timer_subsystems(void)
{
    // this was the setting the original code
    sensor_count = 2;

    init_timer1();
    init_timer2();
    init_timer3();
    init_timer4();
    
    T3CONbits.TON=1;		//battery monitor timer enable
}

void timer_move(int distance, unsigned int speed, int steering_corrector)
{
    d_t_g = distance;
    l_speed = speed;
    r_speed = speed;
    corrector = steering_corrector;
    
	T4CONbits.TON=1;		//right motor timer enable
    T2CONbits.TON=1;		//left motor timer enable
}

bool is_timer_finished_move(void)
{
    return T2CONbits.TON;
}

void timer_fine_to_move_another_cell(void)
{
    d_t_g_flag = 1;
}

void enable_IR_scanning(void)
{
    T1CONbits.TON=1;    // sensors on
}

void disable_IR_scanning(void)
{
    T1CONbits.TON=0;
}




void set_cell_distance(int d)
{
    cell = d;
}

void set_wall_edge_to_crt_distance(int d)
{
    wall_edge_to_crt = d;
}

void set_front_long_threshold(int t)
{
    front_long_threshold = t;
}

void set_front_short_threshold(int t)
{
    front_short_threshold = t;
}

void set_left_side_threshold(int t)
{
    ls_threshold = t;
}

void set_right_side_threshold(int t)
{
    rs_threshold = t;
}

void set_right_45_threshold(int t)
{
    r45_threshold = t;
}

void set_left_45_threshold(int t)
{
    l45_threshold = t;
}

void set_r45_too_close_threshold(int t)
{
    r45_toclose = t;
}

void set_left_45_too_close_threshold(int t)
{
    l45_toclose = t;
}
