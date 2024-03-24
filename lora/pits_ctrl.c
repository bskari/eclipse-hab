//
// Program to control pits pi
//   Button input which when pressed the first time stops the pits process (stops startup
//   and camera scripts, kills running tracker process).  When pressed the second time
//   shuts down the pi.
//
#include <stdio.h>
#include <time.h>
#include <unistd.h>
#include <wiringPi.h>

#define SHUTDOWN    21

int buttonDown;
int buttonPrev;

int buttonPressed() {
   int curButton;
   int n;
   int pressed;

   curButton = (digitalRead(SHUTDOWN) == 0) ? TRUE : FALSE;

   pressed = curButton && buttonPrev && !buttonDown;
   buttonDown = buttonPrev && curButton;
   buttonPrev = curButton;

   return pressed;
}
 

int main(int argc, char** argv) {
  int done = FALSE;
  int pitsRunning = TRUE;

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
       if (pitsRunning) {
         // Kill pits processes
         printf("Killing pits\n");
         system("killall startup");
         system("killall camera");
         system("killall tracker");
         pitsRunning = FALSE;
       } else {
         printf("Shutdown\n");
         done = TRUE;
       }
     }

     // Evaluate every 50 mSec
     (void) usleep((unsigned int) 50000);
  }

  // Initiate shutdown
  system("shutdown now");
  return(0);
}

