CC = gcc
CFLAGS = -Wall -Werror
LDFLAGS = -lwiringPi

all: pi_shutdown pits_ctrl

pi_shutdown: pi_shutdown.o
	# We need to specify this, because gcc wants the linker flags at the
	# end, and by default, Make puts it earlier
	$(CC) $(CFLAGS) pi_shutdown.o -o pi_shutdown $(LDFLAGS)

pits_ctrl: pits_ctrl.o
	$(CC) $(CFLAGS) pits_ctrl.o -o pits_ctrl $(LDFLAGS)

.PHONY: clean
clean:
	rm -f *.o pi_shutdown pits_ctrl
