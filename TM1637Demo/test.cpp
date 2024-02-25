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
