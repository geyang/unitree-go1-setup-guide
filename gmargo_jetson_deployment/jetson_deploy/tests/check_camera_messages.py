import lcm 
import threading
import time
import select
import numpy as np

from jetson_deploy.lcm_types.camera_message_lcmt import camera_message_lcmt


class UnitreeLCMInspector:
    def __init__(self):
        self.lc = lcm.LCM("udpm://239.255.76.67:7667?ttl=255")
        
        low_state_channel = "LCM_Low_State"
        for i in range(6):
            self.low_state_subscription = self.lc.subscribe(f"camera{i}", self._camera_cb)

        self.num_images_received = 0

    def _camera_cb(self, channel, data):
        print(self.num_images_received, channel)
        self.num_images_received += 1
        msg = camera_message_lcmt.decode(data)
        img = np.fromstring(msg.data, dtype=np.uint8)
        img = img.reshape((3, 200, 464)).transpose(1, 2, 0)
        print(img.shape)

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
