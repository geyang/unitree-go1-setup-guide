import lcm 
import threading
import time
import select

from lcm_types.LowCmd import LowCmd
from lcm_types.MotorCmd import MotorCmd
from lcm_types.LowState import LowState
from lcm_types.MotorState import MotorState


class UnitreeLCMInspector:
    def __init__(self):
        self.lc = lcm.LCM("udpm://239.255.76.67:7667?ttl=255")
        
        low_state_channel = "LCM_Low_State"
        self.low_state_subscription = self.lc.subscribe(low_state_channel, self._low_state_cb)

        self.num_low_states = 0

    def _low_state_cb(self, channel, data):
        print(self.num_low_states, channel)
        self.num_low_states += 1
        msg = LowState.decode(data)
        print(msg)

    def poll(self, cb=None):
        t = time.time()
        try:
            while True:
                timeout = 0.01
                rfds, wfds, efds = select.select([self.lc.fileno()], [], [], timeout)
                if rfds:
                    # print("message received!")
                    self.lc.handle()
                    # print(f'Freq {1. / (time.time() - t)} Hz'); t = time.time()
                else:
                    continue
                    # print(f'waiting for message... Freq {1. / (time.time() - t)} Hz'); t = time.time()
                #    if cb is not None:
                #        cb()
        except KeyboardInterrupt:
            pass

    def spin(self):
        self.run_thread = threading.Thread(target=self.poll, daemon=False)
        self.run_thread.start()

if __name__ == "__main__":
    #check_lcm_msgs()
    insp = UnitreeLCMInspector()
    insp.spin()
