//
// Program to shutdown a pi
//
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
#include <wiringPi.h>

#define SHUTDOWN    28

int buttonDown;
int buttonPrev;

int buttonPressed() {
   int curButton;
   int pressed;

   curButton = (digitalRead(SHUTDOWN) == 0) ? TRUE : FALSE;

   pressed = curButton && buttonPrev && !buttonDown;
   buttonDown = buttonPrev && curButton;
   buttonPrev = curButton;

   return pressed;
}
 

int main(int argc, char** argv) {
  int done = FALSE;

  // Initialize button state
  buttonDown = FALSE;
  buttonPrev = FALSE;

  // Initialize wiringPi
  wiringPiSetup();
  pinMode(SHUTDOWN, INPUT);
  pullUpDnControl(SHUTDOWN, PUD_UP);

  while (!done) {
     // Look for camera trigger
     if (buttonPressed()) {
         printf("Shutdown\n");
         done = TRUE;
     }

     // Evaluate every 50 mSec
     (void) usleep((unsigned int) 50000);
  }

  // Initiate shutdown
  system("shutdown now");
  return(0);
}

