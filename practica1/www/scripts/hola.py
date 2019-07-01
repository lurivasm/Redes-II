import sys
import signal
TIMEOUT = 1 # seconds
signal.signal(signal.SIGALRM, input)
signal.alarm(TIMEOUT)

print("\n\nHola", sys.argv[1].split('=')[1].split()[0], "!!")
