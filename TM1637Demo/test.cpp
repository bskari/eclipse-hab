// This is just a test file so that I could test my code on a computer. It has nothing to do with Arduino.
#ifndef ARDUINO

#include "display.hpp"
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <time.h>
#include <curses.h>

void exit() {
  endwin();
}

int main() {
  srand(time(NULL));
  initscr();
  cbreak();
  noecho();
  atexit(exit);

  while (true) {
    tickDisplay();
    usleep(10000);
  }
}

#endif
