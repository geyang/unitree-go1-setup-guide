import os
import pickle as pkl
from matplotlib import pyplot as plt
import time
import imageio
import numpy as np
from tqdm import tqdm
from glob import glob

def create_image_video(log_path):

    data = None
    with open(log_path, 'rb') as file:
        data = pkl.load(file)


    datetime = time.strftime("%Y%m%d-%H%M%S")
    mp4_writer = imageio.get_writer(f'/scratch/gmargo/recordings/deploy_{datetime}.mp4',
                                    fps=50)

    datas = data['hardware_closed_loop'][1]
    print(datas[0].keys())
    for i in range(len(datas)):
        print(i)

        front_image = datas[i]["camera_image_front"]
        bottom_image = datas[i]["camera_image_bottom"]
        rear_image = datas[i]["camera_image_rear"]
        left_image = datas[i]["camera_image_left"]
        right_image = datas[i]["camera_image_right"]


        # fig = plt.figure()
        # plt.imshow(rear_image)
        # # fig.set_dpi(720)
        # fig.tight_layout()
        # fig.canvas.draw()
        # data = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
        # data = data.reshape(fig.canvas.get_width_height()[::-1] + (3,))
        images = [front_image, bottom_image, left_image, right_image, rear_image]
        images = [image for image in images if image is not None]
        if len(images) > 0:
            data = np.concatenate(images, axis=0)
            mp4_writer.append_data(data)
        # plt.close(fig)

def plot_latents(log_path):

    data = None
    with open(log_path, 'rb') as file:
        data = pkl.load(file)


    datetime = time.strftime("%Y%m%d-%H%M%S")
    mp4_writer = imageio.get_writer(f'/scratch/gmargo/recordings/deploy_{datetime}.mp4',
                                    fps=50)

    datas = data['hardware_closed_loop'][1]
    print(datas[0].keys())
    first_latent = datas[0]["latent"]
    latents = np.zeros((len(datas), len(first_latent[0])))
    bottom_images = []
    for i in range(len(datas)):
        latent = datas[i]["latent"]
        latents[i, :] = latent[0]
        bottom_image = datas[i]["camera_image_bottom"]
        if bottom_image is None:
            bottom_image = np.zeros((400, 400))
        bottom_images += [bottom_image]

    plt.figure(figsize=(16, 5))
    plot_step = 50
    num_frames_to_plot = 20
    for l_idx in [0, 1, 2, 3]:
        plt.plot(np.array(range(len(datas))), latents[:, l_idx])
        from matplotlib.offsetbox import TextArea, DrawingArea, OffsetImage, AnnotationBbox
        for i in range(num_frames_to_plot):
            imagebox = OffsetImage(bottom_images[plot_step * i][:, :240], zoom=0.15)
            ab = AnnotationBbox(imagebox, (plot_step * i, -1.3))
            plt.gca().add_artist(ab)
            plt.ylim(-1.5, 1)
    plt.title("Frictions")

    plt.figure()
    for l_idx in [4]:
        plt.plot(np.array(range(len(datas))), latents[:, l_idx])
    plt.title("Restitution")

    plt.figure()
    for l_idx in [5]:
        plt.plot(np.array(range(len(datas))), latents[:, l_idx])
    plt.title("Payload")

    plt.figure()
    for l_idx in [6, 7, 8]:
        plt.plot(np.array(range(len(datas))), latents[:, l_idx])
    plt.title("Velocities")

    plt.figure()
    for l_idx in [9, 10, 11]:
        plt.plot(np.array(range(len(datas))), latents[:, l_idx])
    plt.title("Gravities")

    plt.show()

def render_plot_video(log_dir_root, log_dir, experiment_name):
    log_path = log_dir_root + log_dir + "log.pkl"
    print(log_path)
    data = None
    with open(log_path, 'rb') as file:
        data = pkl.load(file)

    history_length = 100

    directory = f'/scratch/gmargo/recordings/{experiment_name}'
    filename = f'{log_dir[-9:-1]}.mp4'
    if not os.path.exists(directory):
        os.makedirs(directory)
    if os.path.exists(f'{directory}/{filename}'):
        print(f"Skipping {filename} -- already vizualized!")
        return 1
    datetime = time.strftime("%Y%m%d-%H%M%S")
    mp4_writer = imageio.get_writer(f'{directory}/{filename}',
                                    fps=50)

    datas = data['hardware_closed_loop'][1]

    first_latent = datas[0]["latent"]
    latents = np.zeros((history_length + len(datas), len(first_latent[0])))
    images = {"camera_image_bottom": [],
              "camera_image_front": [],
              "camera_image_rear": [],
              "camera_image_left": [],
              "camera_image_right": [], }
    for i in range(len(datas)):
        latent = datas[i]["latent"]
        latents[i+history_length, :] = latent[0]
        for k, v in images.items():
            image = datas[i][k]
            if image is None:
                image = np.zeros((400, 400))
            v += [image]

    import matplotlib.pyplot as plt

    # figure_mosaic = """
    #             AABFG
    #             AADHI
    #             CCCCC
    #             """
    # figure_mosaic = """
    #                 BFGDH
    #                 CCJKK
    #                 """
    figure_mosaic = """
                    KKBD
                    CCFG
                    """

    fig, axs = plt.subplot_mosaic(mosaic=figure_mosaic, figsize=(10, 6))
    # images_to_plot = env.segmentation_images
    imgs = {}
    lines = {}
    imgs["B"] = axs["B"].imshow(np.zeros((10, 10)))
    axs["B"].set_ylabel("Front Camera")
    imgs["F"] = axs["F"].imshow(np.zeros((10, 10)))
    axs["F"].set_ylabel("Left Camera")
    imgs["G"] = axs["G"].imshow(np.zeros((10, 10)))
    axs["G"].set_ylabel("Right Camera")
    imgs["D"] = axs["D"].imshow(np.zeros((10, 10)))
    axs["D"].set_ylabel("Bottom Camera")
    # imgs["H"] = axs["H"].imshow(np.zeros((10, 10)))
    # axs["H"].set_ylabel("Rear Camera")
    # imgs["A"] = axs["A"].imshow(env.render(sensor="rgb", distance=1.5))
    # axs["A"].text(20.0, LeggedRobotCfg.env.recording_height_px - 30,
    #               r"$\mu_s=$" + f"{env.ground_friction_coeffs[0]:.2f}", color="white",
    #               backgroundcolor="grey")

    # imgs["I"] = axs["I"].imshow(np.zeros((10, 10)))
    # axs["I"].set_ylabel("Friction Map")

    # axs["C"].plot(np.linspace((i - ground_frictions_history.shape[0]) * env.dt, i * env.dt,
    #                           ground_frictions_history.shape[0]), ground_frictions_history)
    # axs["C"].set_ylim(0, 1.5)
    # axs["C"].set_xlabel("time (s)")
    # axs["C"].set_ylabel(r"$\mu_s$")
    # axs["C"].set_aspect(1.5)
    #
    # axs["E"].plot(np.linspace((i - velocities_history.shape[0]) * env.dt, i * env.dt,
    #                           velocities_history.shape[0]), velocities_history, color="green")
    # axs["E"].plot(np.linspace((i - velocities_history.shape[0]) * env.dt, i * env.dt,
    #                           velocities_history.shape[0]),
    #               env.commands[0, 0].cpu() * np.ones(velocities_history.shape[0]), color="green",
    #               linestyle="--")
    # axs["E"].set_ylim(0, 3.5)
    # axs["E"].set_xlabel("time (s)")
    # axs["E"].set_ylabel(r"$v_x$ (m/s)")
    # axs["E"].set_aspect(1.0)

    colors = ['blue', 'red', 'green', 'black']
    for color, foot_id in zip(colors, range(4)):
        lines[f"C{foot_id}"], = axs["C"].plot([], [],
                      color=color,
                      linestyle='-.')
    axs["C"].set_xlabel("Timestep")
    axs["C"].set_ylabel("Foot Friction")
    axs["C"].set_ylim(-0.1, 1.1)

    for color, vel_id in zip(colors, range(3)):
        lines[f"K{vel_id}"], = axs["K"].plot([], [],
                      color=color,
                      linestyle='-.')
    axs["K"].set_xlabel("Timestep")
    axs["K"].set_ylabel("Body Velocity")
    axs["K"].set_ylim(-1.5, 1.5)

    # for l in ["A", "B", "D", "F", "G", "H", "I"]:
    for l in ["B", "D", "F", "G"]:
        axs[l].set_xticks([])
        axs[l].set_yticks([])
        axs[l].get_yaxis().set_ticklabels([])
        axs[l].get_xaxis().set_ticklabels([])
    # for l in ["N"]:
    #     axs[l].axis("off")
    plt.suptitle("Multi-Camera Views")
    # plt.suptitle("RGB Images")
    fig.set_dpi(40)
    fig.tight_layout()
    fig.canvas.draw()
    backgrounds = {}
    for ax_key in axs.keys():
        backgrounds[ax_key] = fig.canvas.copy_from_bbox(axs[ax_key].bbox)

    plt.show(block=False)

    for i in tqdm(range(len(datas))):
        latent = datas[i]["latent"]
        latents[i, :] = latent[0]
        import matplotlib.pyplot as plt


        for ax_key in axs.keys():
            fig.canvas.restore_region(backgrounds[ax_key])

        # images_to_plot = env.segmentation_images
        imgs["B"].set_data(images["camera_image_front"][i])
        axs["B"].draw_artist(imgs["B"])
        imgs["F"].set_data(images["camera_image_left"][i])
        axs["F"].draw_artist(imgs["F"])
        imgs["G"].set_data(images["camera_image_right"][i])
        axs["G"].draw_artist(imgs["G"])
        imgs["D"].set_data(images["camera_image_bottom"][i])
        axs["D"].draw_artist(imgs["D"])
        # if LeggedRobotCfg.perception.observe_segmentation:
        # imgs["H"].set_data(images["camera_image_rear"][i])
        # axs["H"].draw_artist(imgs["H"])
        # axs["A"].imshow(env.render(sensor="segmentation", distance=1.5))
        # imgs["A"].set_data(env.render(sensor="rgb", distance=1.5))
        # axs["A"].draw_artist(imgs["A"])

        # imgs["I"].set_data(env.measured_frictions[0].reshape(len(env.cfg.perception.measured_points_x),
        #                                                      len(env.cfg.perception.measured_points_y)).cpu().numpy())
        # axs["I"].draw_artist(imgs["I"])
        colors = ['blue', 'red', 'green', 'black']
        for color, foot_id in zip(colors, range(4)):
            lines[f"C{foot_id}"].set_data((np.array(range(history_length)) + i) * 0.02, latents[i:history_length + i, foot_id] * 0.5 + 0.5)
            axs["C"].draw_artist(lines[f"C{foot_id}"])
            axs["C"].set_xlim(i*0.02, (i+history_length) * 0.02)
        colors = ['blue', 'red', 'green', 'black']
        for color, vel_id in zip(colors, range(3)):
            lines[f"K{vel_id}"].set_data((np.array(range(history_length)) + i) * 0.02,
                                         latents[i:history_length + i, vel_id + 6] * 6)
            axs["K"].draw_artist(lines[f"K{vel_id}"])
            axs["K"].set_xlim(i*0.02, (i+history_length) * 0.02)

        for ax in axs.values():
            fig.canvas.blit(ax)

        data = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
        data = data.reshape(fig.canvas.get_width_height()[::-1] + (3,))
        mp4_writer.append_data(data)
        # plt.close(fig)
        fig.canvas.flush_events()
        # plt.show()

if __name__ == "__main__":
    log_dir_root = "../../logs/"
    experiment_name = "20220523_afternoon_deployment"
    # experiment_name = "20220524_morning_robust_platformer_outside"
    # log_dir = "2022/05_17/00_35_42/"
    # log_dir = "2022/05_17/01_03_39/"
    # log_dir = "20220523_concurrent_jistyleclip_estimation_bonus_100/2022/05_17/00_54_11/"
    # log_dir = "20220523_afternoon_deployment/2022/05_17/00_43_26/"
    log_dir = f"{experiment_name}/2022/05_17/"
    # log_path = log_dir_root + log_dir + "log.pkl"
    # create_image_video(log_path)
    # plot_latents(log_path)


    log_dirs = glob(f"{log_dir_root}{log_dir}/*/", recursive=True)
    input(log_dirs)
    for log_dir in log_dirs:
        try:
            render_plot_video(log_dir[:11], log_dir[11:], experiment_name=experiment_name)
        except FileNotFoundError:
            print(f"Couldn't find log.pkl in {log_dir}")
        except EOFError:
            print(f"Incomplete log.pkl in {log_dir}")