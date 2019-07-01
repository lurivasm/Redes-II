import sys
import signal
TIMEOUT = 1 # seconds
signal.signal(signal.SIGALRM, input)
signal.alarm(TIMEOUT)


celsius = int(sys.argv[1].split('=')[1].split()[0])
fahrenheit = (celsius * 9/5) + 32
print("\n\nLos", celsius, "grados Celsius son", fahrenheit, "grados Fahrenheit")
