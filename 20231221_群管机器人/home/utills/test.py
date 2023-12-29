from threading import Thread
from datetime import datetime
import time


def test(i):
    while True:
        print(i)
        return


for i in range(100000):
    t = Thread(target=test, args=(i,))
    t.start()
