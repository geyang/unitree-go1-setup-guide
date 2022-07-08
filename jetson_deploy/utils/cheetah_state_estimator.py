import math
import select
import threading
import time

import numpy as np

from jetson_deploy.lcm_types.leg_control_data_lcmt import leg_control_data_lcmt
from jetson_deploy.lcm_types.rc_command_lcmt import rc_command_lcmt
from jetson_deploy.lcm_types.state_estimator_lcmt import state_estimator_lcmt
from jetson_deploy.lcm_types.vicon_pose_lcmt import vicon_pose_lcmt
from jetson_deploy.lcm_types.camera_message_lcmt import camera_message_lcmt


def get_rpy_from_quaternion(q):
    w, x, y, z = q
    r = np.arctan2(2 * (w * x + y * z), 1 - 2 * (x ** 2 + y ** 2))
    p = np.arcsin(2 * (w * y - z * x))
    y = np.arctan2(2 * (w * z + x * y), 1 - 2 * (y ** 2 + z ** 2))
    return np.array([r, p, y])


def get_rotation_matrix_from_rpy(rpy):
    """
    Get rotation matrix from the given quaternion.
    Args:
        q (np.array[float[4]]): quaternion [w,x,y,z]
    Returns:
        np.array[float[3,3]]: rotation matrix.
    """
    r, p, y = rpy
    R_x = np.array([[1, 0, 0],
                    [0, math.cos(r), -math.sin(r)],
                    [0, math.sin(r), math.cos(r)]
                    ])

    R_y = np.array([[math.cos(p), 0, math.sin(p)],
                    [0, 1, 0],
                    [-math.sin(p), 0, math.cos(p)]
                    ])

    R_z = np.array([[math.cos(y), -math.sin(y), 0],
                    [math.sin(y), math.cos(y), 0],
                    [0, 0, 1]
                    ])

    rot = np.dot(R_z, np.dot(R_y, R_x))
    return rot


class StateEstimator:
    def __init__(self, lc, use_vicon=False, use_cameras=True):

        # reverse legs
        self.joint_idxs = [3, 4, 5, 0, 1, 2, 9, 10, 11, 6, 7, 8]
        # self.joint_idxs = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

        self.lc = lc

        self.joint_pos = np.zeros(12)
        self.joint_vel = np.zeros(12)
        self.world_lin_vel = np.zeros(3)
        self.world_ang_vel = np.zeros(3)
        self.euler = np.zeros(3)
        self.R = np.eye(3)
        self.R_vicon = np.eye(3)
        self.buf_idx = 0

        self.smoothing_length = 12
        self.deuler_history = np.zeros((self.smoothing_length, 3))
        self.dt_history = np.zeros((self.smoothing_length, 1))
        self.euler_prev = np.zeros(3)
        self.timuprev = time.time()

        self.body_lin_vel = np.zeros(3)
        self.body_ang_vel = np.zeros(3)
        self.smoothing_ratio = 0.2

        self.mode = 0
        self.left_stick = [0, 0]
        self.right_stick = [0, 0]
        self.left_upper_switch = 0
        self.left_lower_left_switch = 0
        self.left_lower_right_switch = 0
        self.right_upper_switch = 0
        self.right_lower_left_switch = 0
        self.right_lower_right_switch = 0
        self.left_upper_switch_pressed = 0
        self.left_lower_left_switch_pressed = 0
        self.left_lower_right_switch_pressed = 0
        self.right_upper_switch_pressed = 0
        self.right_lower_left_switch_pressed = 0
        self.right_lower_right_switch_pressed = 0

        # default trotting gait
        self.cmd_freq = 3.0
        self.cmd_phase = 0.5
        self.cmd_offset = 0.0
        self.cmd_duration = 0.5


        self.init_time = time.time()
        self.received_first_legdata = False

        self.use_vicon = use_vicon
        self.vicon_data_subscription = self.lc.subscribe("cheetah_improbable/cheetah_improbable", self._vicon_cb)
        self.imu_subscription = self.lc.subscribe("state_estimator_data", self._imu_cb)
        self.legdata_state_subscription = self.lc.subscribe("leg_control_data", self._legdata_cb)
        self.rc_command_subscription = self.lc.subscribe("rc_command", self._rc_command_cb)

        if use_cameras:
            for cam_id in [1, 2, 3, 4, 5]:
                self.camera_subscription = self.lc.subscribe(f"camera{cam_id}", self._camera_cb)
        self.camera_image_left = None
        self.camera_image_right = None
        self.camera_image_front = None
        self.camera_image_bottom = None
        self.camera_image_rear = None

        self.position_offset = np.array([10, 10, 0])  # convert from vicon coords to legged_gym coords
        self.body_loc = np.array([0, 0, 0])
        self.body_quat = np.array([0, 0, 0, 1])
        self.platform_loc = np.array([0, 0, 0])
        self.platform_ori = np.array([0, 0, 0])
        self.platform_loc_subscription = self.lc.subscribe("platform_improbable_1/platform_improbable_1",
                                                           self._platform_cb)

    def get_body_linear_vel(self):
        self.body_lin_vel = np.dot(self.R_vicon.T, self.world_lin_vel)
        # self.body_lin_vel = self.smoothing_ratio * np.dot(self.R_vicon.T, self.world_lin_vel) + (1 - self.smoothing_ratio) * self.body_lin_vel
        return self.body_lin_vel

    def get_body_angular_vel(self):
        # self.body_ang_vel = np.dot(self.R_vicon.T, self.world_ang_vel)
        # self.body_ang_vel = np.mean(self.deuler_history / self.dt_history, axis=0)
        self.body_ang_vel = self.smoothing_ratio * np.mean(self.deuler_history / self.dt_history, axis=0) + (
                    1 - self.smoothing_ratio) * self.body_ang_vel
        #print('bal', self.body_ang_vel)
        return self.body_ang_vel

    def get_gravity_vector(self):
        grav = np.dot(self.R.T, np.array([0, 0, -1]))
        #print(grav)
        return grav

    def get_rpy(self):
        return self.euler

    def get_command(self):
        cmd_x = 1 * self.left_stick[1]
        cmd_y = -1 * self.left_stick[0]
        cmd_yaw = -1 * self.right_stick[0]
        cmd_height = 0.0

        min_freq = 1.5
        max_freq = 4.0
        cmd_freq = (1 + self.right_stick[1]) / 2 * (max_freq-min_freq) + min_freq

        # if self.left_upper_switch_pressed:
        #     if self.cmd_phase == 0.5:
        #         self.cmd_phase = 0.0
        #     elif self.cmd_phase == 0.0:
        #         self.cmd_phase = 0.25
        #     else:
        #         self.cmd_phase = 0.5
        #     self.left_upper_switch_pressed = False
        if self.mode == 0:
            self.cmd_phase = 0.5
            self.cmd_offset = 0.0
        elif self.mode == 1:
            self.cmd_phase = 0.0
            self.cmd_offset = 0.0
        elif self.mode == 2:
            self.cmd_phase = 0.25
            self.cmd_offset = 0.0
        elif self.mode == 3:
            self.cmd_phase = 0.0
            self.cmd_offset = 0.5
        elif self.mode == 4:
            self.cmd_phase = 0.0
            self.cmd_offset = 0.3

        # cmd_freq = (3.0 if not self.left_upper_switch else 2.0)
        # cmd_phase = (0.5 if not self.left_lower_left_switch else 0.0)
        # cmd_offset = 0.0
        # cmd_duration = 0.5

        # print(cmd_x, cmd_y)

        return np.array([cmd_x, cmd_y, cmd_yaw, cmd_height, cmd_freq, self.cmd_phase, self.cmd_offset, self.cmd_duration])

    def get_buttons(self):
        return np.array([self.left_lower_left_switch, self.left_upper_switch, self.right_lower_right_switch, self.right_upper_switch])

    def get_dof_pos(self):
        # print("dofposquery", self.joint_pos[self.joint_idxs])
        return self.joint_pos[self.joint_idxs]

    def get_dof_vel(self):
        return self.joint_vel[self.joint_idxs]

    def get_yaw(self):
        return self.euler[2]

    def get_body_loc(self):
        return np.array(self.body_loc) + self.position_offset

    def get_body_quat(self):
        return np.array(self.body_quat)

    def get_platform_loc(self):
        return self.platform_loc + self.position_offset

    def get_platform_ori(self):
        return self.platform_ori

    def get_camera_front(self):
        return self.camera_image_front

    def get_camera_bottom(self):
        return self.camera_image_bottom

    def get_camera_rear(self):
        return self.camera_image_rear

    def get_camera_left(self):
        return self.camera_image_left

    def get_camera_right(self):
        return self.camera_image_right

    def _legdata_cb(self, channel, data):
        # print("update legdata")
        if not self.received_first_legdata:
            self.received_first_legdata = True
            print(f"First legdata: {time.time() - self.init_time}")

        msg = leg_control_data_lcmt.decode(data)
        # print(msg.q)
        self.joint_pos = np.array(msg.q)
        self.joint_vel = np.array(msg.qd)
        # print(f"update legdata {msg.id}")

    def _vicon_cb(self, channel, data):
        # print("update vicon")
        msg = vicon_pose_lcmt.decode(data)
        # self.d_pos_buf[self.buf_idx%12, :] = np.array(msg.translation) - self.d_pos_buf[self.buf_idx%12-1, :]
        # self.d_rot_buf[self.buf_idx%12, :] = get_rpy_from_quaternion(np.array(msg.rotation)) - self.d_rot_buf[self.buf_idx%12-1, :]
        # self.dt_buf[self.buf_idx%12] = msg.timestamp_us - self.dt_buf[self.buf_idx%12-1]
        # self.quat = msg.rotation

        self.world_lin_vel = msg.linear_velocity
        self.world_ang_vel = msg.angular_velocity
        self.body_loc = msg.translation
        self.body_quat = msg.rotation

        # if self.use_vicon:
        self.euler_vicon = msg.euler

        self.R_vicon = get_rotation_matrix_from_rpy(self.euler_vicon)

        # self.buf_idx += 1

    def _platform_cb(self, channel, data):
        # print("update vicon")
        msg = vicon_pose_lcmt.decode(data)
        # self.d_pos_buf[self.buf_idx%12, :] = np.array(msg.translation) - self.d_pos_buf[self.buf_idx%12-1, :]
        # self.d_rot_buf[self.buf_idx%12, :] = get_rpy_from_quaternion(np.array(msg.rotation)) - self.d_rot_buf[self.buf_idx%12-1, :]
        # self.dt_buf[self.buf_idx%12] = msg.timestamp_us - self.dt_buf[self.buf_idx%12-1]
        # self.quat = msg.rotation

        self.platform_loc = msg.translation
        self.platform_ori = msg.euler

    def _imu_cb(self, channel, data):
        # print("update imu")
        msg = state_estimator_lcmt.decode(data)

        # if not self.use_vicon:
        self.euler = np.array(msg.rpy)

        # if not self.use_vicon:
        self.R = get_rotation_matrix_from_rpy(self.euler)

        self.deuler_history[self.buf_idx % self.smoothing_length, :] = msg.rpy - self.euler_prev
        self.dt_history[self.buf_idx % self.smoothing_length] = time.time() - self.timuprev

        self.timuprev = time.time()

        self.buf_idx += 1
        self.euler_prev = np.array(msg.rpy)

    def _sensor_cb(self, channel, data):
        pass

    def _rc_command_cb(self, channel, data):

        msg = rc_command_lcmt.decode(data)


        self.left_upper_switch_pressed = ((msg.left_upper_switch and not self.left_upper_switch) or self.left_upper_switch_pressed)
        self.left_lower_left_switch_pressed = ((msg.left_lower_left_switch and not self.left_lower_left_switch) or self.left_lower_left_switch_pressed)
        self.left_lower_right_switch_pressed = ((msg.left_lower_right_switch and not self.left_lower_right_switch) or self.left_lower_right_switch_pressed)
        self.right_upper_switch_pressed = ((msg.right_upper_switch and not self.right_upper_switch) or self.right_upper_switch_pressed)
        self.right_lower_left_switch_pressed = ((msg.right_lower_left_switch and not self.right_lower_left_switch) or self.right_lower_left_switch_pressed)
        self.right_lower_right_switch_pressed = ((msg.right_lower_right_switch and not self.right_lower_right_switch) or self.right_lower_right_switch_pressed)

        self.mode = msg.mode
        self.right_stick = msg.right_stick
        self.left_stick = msg.left_stick
        self.left_upper_switch = msg.left_upper_switch
        self.left_lower_left_switch = msg.left_lower_left_switch
        self.left_lower_right_switch = msg.left_lower_right_switch
        self.right_upper_switch = msg.right_upper_switch
        self.right_lower_left_switch = msg.right_lower_left_switch
        self.right_lower_right_switch = msg.right_lower_right_switch

        # print(self.right_stick, self.left_stick)

    def _camera_cb(self, channel, data):
        msg = camera_message_lcmt.decode(data)

        img = np.fromstring(msg.data, dtype=np.uint8)
        img = img.reshape((3, 200, 464)).transpose(1, 2, 0)

        cam_id = int(channel[-1])
        if cam_id == 1:
            self.camera_image_front = img
        elif cam_id == 2:
            self.camera_image_bottom = img
        elif cam_id == 3:
            self.camera_image_left = img
        elif cam_id == 4:
            self.camera_image_right = img
        elif cam_id == 5:
            self.camera_image_rear = img
        else:
            print("Image received from camera with unknown ID#!")

        #im = Image.fromarray(img).convert('RGB')

        #im.save("test_image_" + channel + ".jpg")
        #print(channel)

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

    def close(self):
        self.lc.unsubscribe(self.vicon_data_subscription)
        self.lc.unsubscribe(self.legdata_state_subscription)


if __name__ == "__main__":
    import lcm

    lc = lcm.LCM("udpm://239.255.76.67:7667?ttl=255")
    se = StateEstimator(lc)
    se.poll()
