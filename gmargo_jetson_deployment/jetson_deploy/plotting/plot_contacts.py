import os
import pickle as pkl
from matplotlib import pyplot as plt
from matplotlib.patches import FancyBboxPatch
import time
import imageio
import numpy as np
from tqdm import tqdm
from glob import glob

def _get_perp_line(current_seg, out_of_page, linewidth):
    perp = np.cross(current_seg, out_of_page)[0:2]
    perp_unit = _get_unit_vector(perp)
    current_seg_perp_line = perp_unit*linewidth
    return current_seg_perp_line

def _get_unit_vector(vector):
    vector_size = (vector[0]**2 + vector[1]**2)**0.5
    vector_unit = vector / vector_size
    return vector_unit[0:2]

def plot_contacts(log_dir_root, log_dir, experiment_name=None, plot_latents=False, event_locations = []):

    data = None
    log_path = log_dir_root + log_dir + "log.pkl"
    with open(log_path, 'rb') as file:
        data = pkl.load(file)


    datetime = time.strftime("%Y%m%d-%H%M%S")
    mp4_writer = imageio.get_writer(f'/scratch/gmargo/recordings/deploy_{datetime}.mp4',
                                    fps=50)

    datas = data['hardware_closed_loop'][1]
    datas = datas[:800]

    num_latents = datas[0]['latent'].shape[1]

    print(datas[0].keys())
    contact_states = np.zeros((len(datas), 4))
    clock_inputs = np.zeros((len(datas), 4))
    torques = np.zeros((len(datas), 12))
    latents = np.zeros((len(datas), num_latents))
    vel_commands = np.zeros((len(datas), 3))
    angular_vels = np.zeros((len(datas), 3))
    angular_vel_commands = np.zeros((len(datas), 3))
    body_height_commands = np.zeros((len(datas), 3))
    for i in range(len(datas)):
        contact_state = datas[i]["contact_state"]
        contact_states[i, :] = contact_state[0]
        clock_input = datas[i]["clock_inputs"]
        clock_inputs[i, :] = clock_input[0]
        torque = datas[i]["torques"]
        torques[i, :] = torque
        latent = datas[i]["latent"]
        latents[i, :] = latent
        vel_command = datas[i]["body_linear_vel_cmd"]
        vel_commands[i, :2] = vel_command
        angular_vel = datas[i]["body_angular_vel"]
        angular_vels[i, :] = angular_vel
        angular_vel_command = datas[i]["body_angular_vel_cmd"]
        angular_vel_commands[i, 2] = angular_vel_command[0, 0]
        body_height_command = angular_vel_command[0, 1]
        body_height_commands[i, 0] = body_height_command

    if plot_latents:
        fig, axs = plt.subplots(3, 1, figsize=(18, 6))
    else:
        fig, axs = plt.subplots(2, 1, figsize=(18, 3))
    axs = np.array(axs).flatten()
    plot_step = 50
    num_frames_to_plot = 20
    # colors = ["red", "green", "blue", "orange"]
    colors = [(185 / 255.0,  71 / 255.0,   0 / 255.0),
              (137 / 255.0, 141 / 255.0, 141 / 255.0),
              (  0 / 255.0, 156 / 255.0, 222 / 255.0),
              ( 59 / 255.0, 157 / 255.0, 141 / 255.0),
              (240 / 255.0, 179 / 255.0,  35 / 255.0),]

    feet = [0, 1, 2, 3]
    for l_idx, color in zip(feet, colors):
        contact_state = 0
        contact_start = 0


        x = np.array(range(len(datas))) / 50.
        y = np.ones(len(datas)) * 0.0
        z = (clock_inputs[:, l_idx] + 1) / 2

        line_height = 0.3

        num_pts = len(x)
        line_width = 1
        [xs, ys, zs] = [
            np.zeros((num_pts, 2)),
            np.zeros((num_pts, 2)),
            np.zeros((num_pts, 2))
        ]

        dist = 0
        out_of_page = [0, 0, 1]
        for i in range(num_pts):
            # set the colors and the x,y locations of the source line
            xs[i][0] = x[i]
            ys[i][0] = y[i] - line_height / 2 + l_idx
            if i > 0:
                x_delta = x[i] - x[i - 1]
                y_delta = y[i] - y[i - 1]
                seg_length = (x_delta ** 2 + y_delta ** 2) ** 0.5
                dist += seg_length
                zs[i] = z[i]

            # define the offset perpendicular points
            if i == num_pts - 1:
                current_seg = [x[i] - x[i - 1], y[i] - y[i - 1], 0]
            else:
                current_seg = [x[i + 1] - x[i], y[i + 1] - y[i], 0]
            current_seg_perp = _get_perp_line(
                current_seg, out_of_page, line_width)
            if i == 0 or i == num_pts - 1:
                xs[i][1] = xs[i][0] + current_seg_perp[0]
                ys[i][1] = ys[i][0] + line_height #current_seg_perp[1]
                continue
            current_pt = [x[i], y[i]]
            current_seg_unit = _get_unit_vector(current_seg)
            previous_seg = [x[i] - x[i - 1], y[i] - y[i - 1], 0]
            previous_seg_perp = _get_perp_line(
                previous_seg, out_of_page, line_width)
            previous_seg_unit = _get_unit_vector(previous_seg)
            # current_pt + previous_seg_perp + scalar * previous_seg_unit =
            # current_pt + current_seg_perp - scalar * current_seg_unit =
            scalar = (
                    (current_seg_perp - previous_seg_perp) /
                    (previous_seg_unit + current_seg_unit)
            )
            new_pt = current_pt + previous_seg_perp + scalar[0] * previous_seg_unit
            xs[i][1] = new_pt[0]
            ys[i][1] = ys[i][0] + line_height

        cm = plt.get_cmap("binary")
        try:
            axs[1].pcolormesh(xs, ys, zs, shading='gouraud', cmap=cm)
        except ValueError:
            print("warning, invalid value encountered, could not plot!")

        for i in range(contact_states.shape[0]):
            if contact_states[i, l_idx] > 0 and contact_state == 0:
                contact_start = i / 50.
                contact_state = 1
            elif (contact_states[i, l_idx] == 0 and contact_state > 0):
                contact_state = 0
                xmin = contact_start
                ymin = -0.2  + l_idx
                xmax = i / 50.
                ymax = 0.2  + l_idx
                p_fancy = FancyBboxPatch((xmin, ymin),
                                         abs(xmax - xmin), abs(ymax - ymin),
                                         boxstyle="round,pad=0.0",
                                         fc=colors[l_idx],
                                         ec=colors[l_idx],
                                         alpha=0.7)
                axs[1].add_patch(p_fancy)

        # axs[l_idx].plot(np.array(range(len(datas))), contact_states[:, l_idx], linestyle='-', color=color)
        # axs[l_idx].plot(np.array(range(len(datas))), (clock_inputs[:, l_idx] + 1) / 2, linestyle='--', color=color)
    # plt.title("Contact States")

    # axs[1].axis('off')
    axs[1].set_xlim(0, len(datas) / 50.)
    axs[1].set_ylabel("Contact States", labelpad=16)
    axs[1].spines.right.set_visible(False)
    axs[1].spines.top.set_visible(False)
    # axs[1].set_yticks([])
    y_ticks_labels = ["", "RF", "RR", "LF", "LR"]
    axs[1].set_yticklabels(y_ticks_labels, rotation='horizontal')

    axs[0].plot(np.array(range(len(datas))), torques)
    axs[0].set_xlim(0, len(datas))
    axs[0].set_ylim(-27, 27)
    axs[0].set_ylabel("Joint Torques (N-m)", labelpad=9)
    axs[0].spines.right.set_visible(False)
    axs[0].spines.top.set_visible(False)
    axs[0].set_xticks([])


    if plot_latents:
        latent_colors = [colors[0], colors[3], colors[4]]
        # plot_state = "angular"
        # plot_state = "linear"
        plot_state = "height"
        if plot_state == "linear":
            for i in range(3):
                axs[2].plot(np.array(range(len(datas))), 6.0 * latents[:, -6+i], color=latent_colors[i])
            for i in range(3):
                axs[2].plot(np.array(range(len(datas))), vel_commands[:, i], linestyle='--', color=latent_colors[i])
            axs[2].set_ylim(-1.0, 2.5)
            axs[2].set_xlim(0, len(datas))
            axs[2].set_ylabel("Body Velocity Estimate", labelpad=7)
            axs[2].spines.right.set_visible(False)
            axs[2].spines.top.set_visible(False)
            axs[2].set_xticks([])
            axs[2].legend(["x-axis", "y-axis", "z-axis"])
        elif plot_state == "angular":
            for i in range(3):
                axs[2].plot(np.array(range(len(datas))), angular_vels[:, i], color=latent_colors[i])
            for i in range(3):
                axs[2].plot(np.array(range(len(datas))), angular_vel_commands[:, i], linestyle='--', color=latent_colors[i])
            axs[2].set_ylim(-1.0, 5.0)
            axs[2].set_xlim(0, len(datas))
            axs[2].set_ylabel("Body Velocity Estimate", labelpad=7)
            axs[2].spines.right.set_visible(False)
            axs[2].spines.top.set_visible(False)
            axs[2].set_xticks([])
            axs[2].legend(["x-axis", "y-axis", "z-axis"])
        elif plot_state == "height":
            axs[2].plot(np.array(range(len(datas))), latents[:, -7] * 0.3 + 0.3, color=latent_colors[0])
            axs[2].plot(np.array(range(len(datas))), body_height_commands[:, 0] * 2 + 0.30, linestyle='--', color=latent_colors[0])
            # axs[2].plot(np.array(range(len(datas))), angular_vels[:, 2], color=latent_colors[1])
            # axs[2].plot(np.array(range(len(datas))), angular_vel_commands[:, 2], linestyle='--',
            #             color=latent_colors[1])
            axs[2].set_ylim(0.25, 0.40)
            # axs[2].set_ylim(-5.0, 5.0)
            axs[2].set_xlim(0, len(datas))
            axs[2].set_ylabel("Body Height Estimate", labelpad=7)
            axs[2].spines.right.set_visible(False)
            axs[2].spines.top.set_visible(False)
            axs[2].set_xticks([])
            axs[2].legend(["true height", "command height"])



        for event_location in event_locations:
            rect = plt.Rectangle((event_location, 0.1), width=65, height=3.2 + fig.subplotpars.wspace,
                                 transform=axs[2].get_xaxis_transform(), clip_on=False,
                                 edgecolor=colors[4], linestyle='--', facecolor="none", linewidth=3)
            axs[2].add_patch(rect)

    plt.tight_layout()


    # plt.figure()
    # for l_idx in [6, 7, 8]:
    #     plt.plot(np.array(range(len(datas))), latents[:, l_idx])
    # plt.title("Velocities")
    #
    # plt.figure()
    # for l_idx in [9, 10, 11]:
    #     plt.plot(np.array(range(len(datas))), latents[:, l_idx])
    # plt.title("Gravities")

    plt.savefig(log_dir_root + log_dir + "contacts.png")
    plt.savefig(log_dir_root + log_dir + "contacts.pdf")


if __name__ == "__main__":
    log_dir_root = "../../logs/"
    # experiment_name = "20220523_afternoon_deployment"
    # experiment_name = "20220524_morning_robust_platformer_outside"
    # experiment_name = "20220602_afternoon_contact_inspection"
    # experiment_name = "20220605_indoor_gaitcycle"
    experiment_name = "20220606_afternoon"
    experiment_name = "20220606_indoor_gaitcycle"
    experiment_name = "20220607_afternoon"
    experiment_name = "20220608_evening"
    experiment_name = "20220610_morning"
    # log_dir = "2022/05_17/00_35_42/"
    # log_dir = "2022/05_17/01_03_39/"
    # log_dir = "20220523_concurrent_jistyleclip_estimation_bonus_100/2022/05_17/00_54_11/"
    # log_dir = "20220523_afternoon_deployment/2022/05_17/00_43_26/"
    log_dir = f"{experiment_name}/2022/05_17/"
    # log_path = log_dir_root + log_dir + "log.pkl"
    # create_image_video(log_path)
    # plot_latents(log_path)


    log_dirs = glob(f"{log_dir_root}{log_dir}/*/", recursive=True)
    # input(log_dirs)
    for log_dir in log_dirs:
        try:
            plot_contacts(log_dir[:11], log_dir[11:], experiment_name=experiment_name, plot_latents=True, event_locations=[])
        except FileNotFoundError:
            print(f"Couldn't find log.pkl in {log_dir}")
        except EOFError:
            print(f"Incomplete log.pkl in {log_dir}")


    plt.show()