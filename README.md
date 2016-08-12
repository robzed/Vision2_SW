# Vision2_SW

This is the code for my Stepper-based mouse Micromouse, which solves 5x5 and 16x16 mazes. 

The base hardware was originally built by Ken Hewitt, I've added a Raspberry Pi and a camera to this 
design, and made various minor modications.


## Architecture

The Raspberry Pi does all mapping, move calculations, and more.

The I/O co-processor is a dsPIC does low-level stepper timing and analogue sensor reading and 
communicates with the Raspberry Pi using a serial interface and a basic command/event language 
between the two microprocessors.

All timing less than 10ms is done by the dsPIC and no attempt has been made yet to do any 
real-time work on the Raspberry Pi.


## License

All the Controller Code (which runs on a Raspberry Pi) is released under the GPL v2 license.

The I/O processor - please see individual files. Some of the low level hardware I/O functions 
were based code from a maze-solver program originally written by someone who had a duplicate of 
Ken's base mouse. He had all the control code running on the dsPIC. My plan is to replace all 
this code eventually, but for the moment I wouldn't base a new project on the files 'io_ports.h', 
'timer_interrupts.c' and 'hardware.c'. The rest of the code I believe is either generic dsPIC 
setup code or is original code by me released under the GPLv2 (and marked as such) so will be 
safe to reuse. 

