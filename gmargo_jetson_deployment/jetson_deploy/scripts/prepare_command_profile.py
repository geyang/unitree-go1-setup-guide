"""
A script for declaring predefined gait sequences.
They are saved as .yaml files in the command_profiles folder.
"""

import json
import numpy as np

def write_gait_to_file(commands, filename):
        commands_dict = {"x_vel_cmd": commands[:, 0].tolist(),
                         "y_vel_cmd": commands[:, 1].tolist(),
                         "yaw_vel_cmd": commands[:, 2].tolist(),
                         "height_cmd": commands[:, 3].tolist(),
                         "frequency_cmd": commands[:, 4].tolist(),
                         "offset_cmd": commands[:, 5].tolist(),
                         "phase_cmd": commands[:, 6].tolist(),
                         "bound_cmd": commands[:, 7].tolist(),
                         "duration_cmd": commands[:, 8].tolist(),
                         }

        with open(f'../command_profiles/{filename}', 'w') as outfile:
                json.dump(commands_dict, outfile, indent=1)#, default_flow_style=False)

def create_dynamic_jump_profile(dt, max_time_s):
        import numpy as np
        import torch

        # max_timestep = int(max_time_s / dt)

        jump_steps = 50
        transition_steps = 0
        accel_steps = 99
        steady_steps = 500
        total_steps = accel_steps * 2 + transition_steps * 2 + jump_steps + steady_steps
        total_time_s = total_steps / dt
        commands = np.zeros((total_steps, 9))

        max_vel = 2.5
        min_freq = 2.0
        max_freq = 3.5

        height = 0.0
        height_sequence = [height] * total_steps

        initial_offset = 0.5 #0.4
        trot_duration = 0.5
        jump_duration = 0.5

        # acceleration
        vel_sequence = [i / accel_steps * max_vel for i in range(accel_steps)]
        freq_sequence = [min_freq + i / accel_steps * (max_freq - min_freq) for i in range(accel_steps)]
        offset_sequence = [initial_offset] * accel_steps
        phase_sequence = [0.0] * accel_steps
        bound_sequence = [0.0] * accel_steps
        duration_sequence = [trot_duration] * accel_steps

        # transition
        # vel_sequence += [max_vel + i / transition_steps * 1.0 for i in range(transition_steps)]
        vel_sequence += [max_vel] * transition_steps
        freq_sequence += [max_freq - i / transition_steps * (max_freq - min_freq) for i in range(transition_steps)]
        offset_sequence += [initial_offset - i / transition_steps * initial_offset for i in range(transition_steps)]
        phase_sequence += [0.0] * transition_steps
        bound_sequence += [0.0] * transition_steps
        duration_sequence += [trot_duration] * transition_steps

        # jump
        vel_sequence += [max_vel] * jump_steps
        freq_sequence += [min_freq] * jump_steps
        offset_sequence += [0.0] * jump_steps
        phase_sequence += [0.0] * jump_steps
        bound_sequence += [0.0] * jump_steps
        duration_sequence += [jump_duration] * jump_steps

        # transition
        # vel_sequence += [3.5 - i / transition_duration_steps * 1.0 for i in range(transition_duration_steps)]
        vel_sequence += [max_vel] * transition_steps
        freq_sequence += [min_freq + i / transition_steps * (max_freq - min_freq) for i in range(transition_steps)]
        offset_sequence += [i / transition_steps * initial_offset for i in range(transition_steps)]
        phase_sequence += [0.0] * transition_steps
        bound_sequence += [0.0] * transition_steps
        duration_sequence += [trot_duration] * transition_steps

        # deceleration
        vel_sequence += [max_vel - i / accel_steps * max_vel for i in range(accel_steps)]
        freq_sequence += [max_freq - i / accel_steps * (max_freq - min_freq) for i in range(accel_steps)]
        offset_sequence += [initial_offset] * accel_steps
        phase_sequence += [0.0] * accel_steps
        bound_sequence += [0.0] * accel_steps
        duration_sequence += [trot_duration] * accel_steps

        # steady state
        vel_sequence += [0.0] * steady_steps
        freq_sequence += [min_freq] * steady_steps
        offset_sequence += [initial_offset] * steady_steps
        phase_sequence += [0.0] * steady_steps
        bound_sequence += [0.0] * steady_steps
        duration_sequence += [0.5] * steady_steps


        commands[:len(vel_sequence), 0] = vel_sequence
        commands[:len(height_sequence), 3] = height_sequence
        commands[:len(freq_sequence), 4] = freq_sequence
        commands[:len(offset_sequence), 5] = offset_sequence
        commands[:len(bound_sequence), 6] = bound_sequence
        commands[:len(phase_sequence), 7] = phase_sequence
        commands[:len(duration_sequence), 8] = duration_sequence

        return commands

def create_dance_thelonious_monk(dt, max_time_s):
        intro_cw = ([
                            # {"seconds": 1.0, "vel": 0.0, "spin": 0.0, "frequency": 1.5, "offset": 0.25, "phase": 0.0, "bound": 0.0, "duration": 0.5},
                            # {"seconds": 0.5, "vel": 0.0, "spin": 2.0, "frequency": 3.0, "offset": 0.0, "phase": 0.0, "bound": 0.0, "duration": 0.5}
                            {"seconds": 0.33, "vel": 0.0, "spin": 0.0, "frequency": 3.0, "offset": 0.5, "phase": 0.0,
                             "bound": 0.0, "duration": 0.5, "height": 0.0},
                            {"seconds": 0.33, "vel": 0.0, "spin": 0.0, "frequency": 3.0, "offset": 0.0, "phase": 0.0,
                             "bound": 0.0, "duration": 0.5, "height": 0.0},
                            {"seconds": 0.66, "vel": 0.0, "spin": 3.0, "frequency": 1.5, "offset": 0.0, "phase": 0.0,
                             "bound": 0.0, "duration": 0.5, "height": 0.0},
                            # walk it out
                            # {"seconds": 1.0, "vel": 0.0, "spin": 0.0, "frequency": 1.5, "offset": 0.0, "phase": 0.5, "bound": 0.0, "duration": 0.5},
                            # {"seconds": 0.5, "vel": 0.0, "spin": -2.0, "frequency": 3.0, "offset": 0.5, "phase": 0.0, "bound": 0.0, "duration": 0.5},
                            # {"seconds": 1.0, "vel": 0.0, "spin": 0.0, "frequency": 3.0, "offset": 0.0, "phase": 0.0, "bound": 0.0, "duration": 0.5},
                            # {"seconds": 1.0, "vel": 0.0, "spin": 0.0, "frequency": 3.0, "offset": 0.0, "phase": 0.0, "bound": 0.0, "duration": 0.5},
                    ] * 6 + \
                    [
                            {"seconds": 2.66, "vel": -0.5, "spin": -2.36, "frequency": 1.5, "offset": 0.0, "phase": 0.0,
                             "bound": 0.5, "duration": 0.5, "height": 0.15},
                    ])

        intro_ccw = ([
                             # {"seconds": 1.0, "vel": 0.0, "spin": 0.0, "frequency": 1.5, "offset": 0.25, "phase": 0.0, "bound": 0.0, "duration": 0.5},
                             # {"seconds": 0.5, "vel": 0.0, "spin": 2.0, "frequency": 3.0, "offset": 0.0, "phase": 0.0, "bound": 0.0, "duration": 0.5}
                             {"seconds": 0.333, "vel": 0.0, "spin": 0.0, "frequency": 3.0, "offset": 0.5, "phase": 0.0,
                              "bound": 0.0, "duration": 0.5, "height": 0.0},
                             {"seconds": 0.333, "vel": 0.0, "spin": 0.0, "frequency": 3.0, "offset": 0.0, "phase": 0.0,
                              "bound": 0.0, "duration": 0.5, "height": 0.0},
                             {"seconds": 0.666, "vel": 0.0, "spin": -2.0, "frequency": 1.5, "offset": 0.0, "phase": 0.0,
                              "bound": 0.0, "duration": 0.5, "height": 0.0},
                             # walk it out
                             # {"seconds": 1.0, "vel": 0.0, "spin": 0.0, "frequency": 1.5, "offset": 0.0, "phase": 0.5, "bound": 0.0, "duration": 0.5},
                             # {"seconds": 0.5, "vel": 0.0, "spin": -2.0, "frequency": 3.0, "offset": 0.5, "phase": 0.0, "bound": 0.0, "duration": 0.5},
                             # {"seconds": 1.0, "vel": 0.0, "spin": 0.0, "frequency": 3.0, "offset": 0.0, "phase": 0.0, "bound": 0.0, "duration": 0.5},
                             # {"seconds": 1.0, "vel": 0.0, "spin": 0.0, "frequency": 3.0, "offset": 0.0, "phase": 0.0, "bound": 0.0, "duration": 0.5},
                     ] * 6 + \
                     [
                             {"seconds": 2.666, "vel": -0.5, "spin": 2.36, "frequency": 1.5, "offset": 0.0,
                              "phase": 0.0,
                              "bound": 0.5, "duration": 0.5, "height": 0.15},
                     ])

        # 8 or 9 measures?
        bounce = [{"seconds": 11.333, "vel": 0.0, "spin": 0.0, "frequency": 3.0, "offset": 0.0, "phase": 0.5,
                   "bound": 0.0, "duration": 0.5, "height": 0.2, "height_period": 1.333}]

        dance_moves = intro_cw + intro_ccw + bounce + intro_cw + bounce

        # acceleration
        vel_sequence = []
        spin_sequence = []
        height_sequence = []
        freq_sequence = []
        offset_sequence = []
        phase_sequence = []
        bound_sequence = []
        duration_sequence = []

        for dance_move in dance_moves:
                num_steps = int(dance_move["seconds"] * 50)
                vel_sequence += [dance_move["vel"] for i in range(num_steps)]
                spin_sequence += [dance_move["spin"] for i in range(num_steps)]
                freq_sequence += [dance_move["frequency"] for i in range(num_steps)]
                offset_sequence += [dance_move["offset"] for i in range(num_steps)]
                phase_sequence += [dance_move["phase"] for i in range(num_steps)]
                bound_sequence += [dance_move["bound"] for i in range(num_steps)]
                duration_sequence += [dance_move["duration"] for i in range(num_steps)]
                if "height_period" in dance_move.keys():
                        height_period = dance_move["height_period"]
                        height_sequence += [dance_move["height"] * np.sin(
                                2 * np.pi * i / num_steps * dance_move["seconds"] / height_period) for i in
                                            range(num_steps)]
                else:
                        height_sequence += [dance_move["height"] for i in range(num_steps)]

        commands = np.zeros((len(vel_sequence), 9))

        commands[:len(vel_sequence), 0] = vel_sequence
        commands[:len(spin_sequence), 2] = spin_sequence
        commands[:len(height_sequence), 3] = height_sequence
        commands[:len(freq_sequence), 4] = freq_sequence
        commands[:len(offset_sequence), 5] = offset_sequence
        commands[:len(phase_sequence), 6] = phase_sequence
        commands[:len(bound_sequence), 7] = bound_sequence
        commands[:len(duration_sequence), 8] = duration_sequence

        return commands

def create_stationary_gait_cycle(dt, max_time_s):
        import numpy as np
        import torch

        steps_per_phase = 100
        total_steps = steps_per_phase * 8
        total_time_s = total_steps * dt

        commands = np.zeros((total_steps, 9))

        vel = 0.0 # 2.3
        low_freq = 2.5
        high_freq = 4.0
        duration = 0.5

        # trot
        vel_sequence = [vel] * steps_per_phase
        freq_sequence = [low_freq] * steps_per_phase
        offset_sequence = [0.5] * steps_per_phase
        phase_sequence = [0.0] * steps_per_phase
        bound_sequence = [0.0] * steps_per_phase
        duration_sequence = [duration] * steps_per_phase

        vel_sequence += [vel] * steps_per_phase
        freq_sequence += [high_freq] * steps_per_phase
        offset_sequence += [0.5] * steps_per_phase
        phase_sequence += [0.0] * steps_per_phase
        bound_sequence += [0.0] * steps_per_phase
        duration_sequence += [duration] * steps_per_phase

        # pronk
        vel_sequence += [vel] * steps_per_phase
        freq_sequence += [low_freq] * steps_per_phase
        offset_sequence += [0.0] * steps_per_phase
        phase_sequence += [0.0] * steps_per_phase
        bound_sequence += [0.0] * steps_per_phase
        duration_sequence += [duration] * steps_per_phase

        vel_sequence += [vel] * steps_per_phase
        freq_sequence += [high_freq] * steps_per_phase
        offset_sequence += [0.0] * steps_per_phase
        phase_sequence += [0.0] * steps_per_phase
        bound_sequence += [0.0] * steps_per_phase
        duration_sequence += [duration] * steps_per_phase

        # pace
        vel_sequence += [vel] * steps_per_phase
        freq_sequence += [low_freq] * steps_per_phase
        offset_sequence += [0.0] * steps_per_phase
        phase_sequence += [0.5] * steps_per_phase
        bound_sequence += [0.0] * steps_per_phase
        duration_sequence += [duration] * steps_per_phase

        vel_sequence += [vel] * steps_per_phase
        freq_sequence += [high_freq] * steps_per_phase
        offset_sequence += [0.0] * steps_per_phase
        phase_sequence += [0.5] * steps_per_phase
        bound_sequence += [0.0] * steps_per_phase
        duration_sequence += [duration] * steps_per_phase

        # bound
        vel_sequence += [vel] * steps_per_phase
        freq_sequence += [low_freq] * steps_per_phase
        offset_sequence += [0.0] * steps_per_phase
        phase_sequence += [0.0] * steps_per_phase
        bound_sequence += [0.5] * steps_per_phase
        duration_sequence += [duration] * steps_per_phase

        vel_sequence += [vel] * steps_per_phase
        freq_sequence += [high_freq] * steps_per_phase
        offset_sequence += [0.0] * steps_per_phase
        phase_sequence += [0.0] * steps_per_phase
        bound_sequence += [0.5] * steps_per_phase
        duration_sequence += [duration] * steps_per_phase

        commands[:len(vel_sequence), 0] = vel_sequence
        commands[:len(freq_sequence), 4] = freq_sequence
        commands[:len(offset_sequence), 5] = offset_sequence
        commands[:len(phase_sequence), 6] = phase_sequence
        commands[:len(bound_sequence), 7] = bound_sequence
        commands[:len(duration_sequence), 8] = duration_sequence

        return commands

def create_stationary_trot(dt, max_time_s):
        import numpy as np
        import torch

        steps_per_phase = 200
        total_steps = steps_per_phase * 2
        total_time_s = total_steps * dt

        commands = np.zeros((total_steps, 9))

        vel = 0.0 # 2.3
        low_freq = 2.5
        high_freq = 4.0
        low_height = -0.2
        high_height = 0.1
        duration = 0.5

        # trot
        vel_sequence = [vel] * steps_per_phase
        height_sequence = [low_height] * (steps_per_phase // 2) + [high_height] * (steps_per_phase // 2)
        freq_sequence = [low_freq] * steps_per_phase
        offset_sequence = [0.5] * steps_per_phase
        phase_sequence = [0.0] * steps_per_phase
        bound_sequence = [0.0] * steps_per_phase
        duration_sequence = [duration] * steps_per_phase

        vel_sequence += [vel] * steps_per_phase
        height_sequence += [low_height] * (steps_per_phase // 2) + [high_height] * (steps_per_phase // 2)
        freq_sequence += [high_freq] * steps_per_phase
        offset_sequence += [0.5] * steps_per_phase
        phase_sequence += [0.0] * steps_per_phase
        bound_sequence += [0.0] * steps_per_phase
        duration_sequence += [duration] * steps_per_phase


        commands[:len(vel_sequence), 0] = vel_sequence
        commands[:len(height_sequence), 3] = height_sequence
        commands[:len(freq_sequence), 4] = freq_sequence
        commands[:len(offset_sequence), 5] = offset_sequence
        commands[:len(phase_sequence), 6] = phase_sequence
        commands[:len(bound_sequence), 7] = bound_sequence
        commands[:len(duration_sequence), 8] = duration_sequence

        return commands

def create_frequency_sweep(dt, max_time_s):
        import numpy as np
        import torch

        total_steps = 400
        total_time_s = total_steps * dt

        commands = np.zeros((total_steps, 9))

        low_freq = 1.5
        high_freq = 4.0
        low_height = -0.2
        high_height = 0.1
        duration = 0.5

        # trot
        vel_sequence = [0] * total_steps
        height_sequence = [0.0] * total_steps
        freq_sequence = [high_freq - (high_freq - low_freq) * i / (total_steps // 2) for i in range((total_steps // 2))]
        freq_sequence += [low_freq + (high_freq - low_freq) * i / (total_steps // 2) for i in range((total_steps // 2) )]
        offset_sequence = [0.5] * total_steps
        phase_sequence = [0.0] * total_steps
        bound_sequence = [0.0] * total_steps
        duration_sequence = [0.5] * total_steps


        commands[:len(vel_sequence), 0] = vel_sequence
        commands[:len(height_sequence), 3] = height_sequence
        commands[:len(freq_sequence), 4] = freq_sequence
        commands[:len(offset_sequence), 5] = offset_sequence
        commands[:len(phase_sequence), 6] = phase_sequence
        commands[:len(bound_sequence), 7] = bound_sequence
        commands[:len(duration_sequence), 8] = duration_sequence

        return commands


def create_spin_test(dt, max_time_s):
        import numpy as np
        import torch

        accel_steps = 50
        high_steps = 300
        decel_steps = 50
        total_steps = accel_steps + high_steps + decel_steps
        total_time_s = total_steps * dt

        commands = np.zeros((total_steps, 9))

        max_yaw = 5.0

        vel_sequence = [0] * total_steps
        height_sequence = [0.0] * total_steps
        freq_sequence = [2.5] * total_steps
        offset_sequence = [0.5] * (total_steps // 2) + [0.0] * (total_steps // 2)
        phase_sequence = [0.0] * total_steps
        bound_sequence = [0.0] * total_steps
        duration_sequence = [0.5] * total_steps

        yaw_vel_sequence = [max_yaw * i / (total_steps // 2) for i in range((total_steps // 2))]
        yaw_vel_sequence += [max_yaw - max_yaw * i / (total_steps // 2) for i in range((total_steps // 2))]


        commands[:len(vel_sequence), 0] = vel_sequence
        commands[:len(yaw_vel_sequence), 2] = yaw_vel_sequence
        commands[:len(height_sequence), 3] = height_sequence
        commands[:len(freq_sequence), 4] = freq_sequence
        commands[:len(offset_sequence), 5] = offset_sequence
        commands[:len(phase_sequence), 6] = phase_sequence
        commands[:len(bound_sequence), 7] = bound_sequence
        commands[:len(duration_sequence), 8] = duration_sequence

        return commands

if __name__ == "__main__":

        commands = create_dynamic_jump_profile(dt=1./50., max_time_s=10.)
        write_gait_to_file(commands, "jump_sequence_max_vel_3_f2.json")

        # commands = create_stationary_gait_cycle(dt=1. / 50., max_time_s=10.)
        # write_gait_to_file(commands, "stationary_gait_cycle.json")

        # commands = create_stationary_trot(dt=1. / 50., max_time_s=10.)
        # write_gait_to_file(commands, "stationary_trot.json")

        # commands = create_frequency_sweep(dt=1. / 50., max_time_s=10.)
        # write_gait_to_file(commands, "frequency_sweep_trot.json")

        # commands = create_spin_test(dt=1. / 50., max_time_s=10.)
        # write_gait_to_file(commands, "spin_test_trot.json")

        # commands = create_dance_thelonious_monk(dt=1./50., max_time_s=100.)
        # write_gait_to_file(commands, "dance_in_walked_bud.json")
