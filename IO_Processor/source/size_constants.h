/* 
 * File:   size_constants.h
 * Author: rob
 *
 * Created on April 10, 2016, 10:06 AM
 */

#ifndef SIZE_CONSTANTS_H
#define	SIZE_CONSTANTS_H

#ifdef	__cplusplus
extern "C" {
#endif

#define cell	347			//adjust these values for cell distance		


#define wall_edge_to_crt	230	//front error corection value
								//should equal distance from wall edge to
								//centre of square 

    
    
#define front_long_threshold 15		//adjusted once data output vis RS232
#define front_short_threshold 50	//is available 
#define ls_threshold		200
#define rs_threshold		200
#define r45_threshold		540
#define l45_threshold		360
#define r45_toclose		760
#define l45_toclose		580

// figures just for test
//#define front_long_threshold    15
//#define front_short_threshold   50
//#define ls_threshold            200
//#define rs_threshold            200
//#define r45_threshold           360
//#define l45_threshold           360
//#define r45_toclose             540
//#define l45_toclose             540


#ifdef	__cplusplus
}
#endif

#endif	/* SIZE_CONSTANTS_H */

