
# pre-defined string lengths...
TINY_STRING = 64
LIL_STRING = 128
SMALL_STRING = 256
BIG_STRING = 512
HUGE_STRING = 1024


CARDINALITY_MIN_CHOICES = [(str(i), str(i)) for i in range(0, 11)]
CARDINALITY_MAX_CHOICES = [('N', 'N')] + [(str(i), str(i)) for i in range(0, 11)]