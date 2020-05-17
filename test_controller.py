#!/usr/bin/env python
import time
import pigpio
import ir_hasher

def callback(hash):
    if hash not in hash2key:
        print('Unrecognized key')
    else:
        print(f'{hash2key[hash]} was pressed');


hash2key = {
      2209067173: "KEY_1",  2475776301: "KEY_2",    811016773: "KEY_3",
      22461621: "KEY_4",    2338142909: "KEY_6",    3131250093: "KEY_HASHTAG",
      1036916573: "KEY_5",  3502206629: "KEY_0",    4158662973: "KEY_9",
      383079973: "KEY_7",   2749130309: "KEY_8",    2266238925: "KEY_STAR",
                            435909485: "UP",
      430130277: "LEFT",    3072262781:"OK",        3890174357:"RIGHT",
                            2654424341:"DOWN"}

pi = pigpio.pi()
ir = ir_hasher.hasher(pi, 17, callback, 5)

time.sleep(30)

pi.stop()
