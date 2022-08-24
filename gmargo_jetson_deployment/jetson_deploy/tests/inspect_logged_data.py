import copy
import pickle as pkl
import os

import numpy as np

if __name__ == "__main__":
    #filename = '/data/pulkitag/models/gabe/unitree_logs/deploy_2021_11_08-07_26.pkl'
    logdir= '/scratch/gmargo/jetson-model-deployment/logs/vel_2.0/yaw_0.0/deploy/'
    filenames = os.listdir(logdir)
    filenames = [os.path.join(logdir, filename) for filename in filenames if filename[-3:] == "pkl"]

    for filename in filenames:

        with open(filename, 'rb') as file:
            try:
                data = pkl.load(file)
            except EOFError:
                print(f"{filename} corrupted, skipping!")
                continue
            cfg, infos = data['hardware_closed_loop']
            print(f'"number of timesteps: {len(infos)}')

            from matplotlib import pyplot as plt
            print(infos[0].keys())

            try:
                front_frames = [infos[i]["rect_image_front"][...,::-1] for i in range(len(infos))]
            except:
                print("no front frames")
            try:
                bottom_frames = [infos[i]["rect_image_bottom"][..., ::-1] for i in range(len(infos))]
                num_frames_to_plot = min(24, len(bottom_frames) // plot_step)
            except:
                print("no bottom frames")
                num_frames_to_plot = 0
            try:
                concat_frames = [np.concatenate((bottom_frames[i], front_frames[i]), axis=0) for i in range(len(infos))]
            except:
                print("no frames")
            latents = np.array([infos[i]["latent"][0] for i in range(len(infos))])
            commands = np.array([infos[i]["body_linear_vel_cmd"][0] for i in range(len(infos))])

            plot_step = 10

            rows = 4
            cols = num_frames_to_plot // rows
            #fig, axs = plt.subplots(3*rows, num_frames_to_plot // rows)
            # for i in range(num_frames_to_plot):
            #     row = i // cols * 3
            #     col = i % cols
            #     print(row, col, i)
            #     axs[0+row, col].imshow(infos[plot_step*i]["rect_image_bottom"][...,::-1])
            #     axs[0+row, col].set_title(f"t={plot_step*i/50}s")
            #     axs[1+row, col].imshow(infos[plot_step*i]["rect_image_front"][...,::-1])
            #     print( latents[plot_step*i])
            #     axs[2+row, col].bar(range(len(latents[plot_step*i])), latents[plot_step*i])
            #     axs[2+row, col].set_ylim(-1, 1)

            print(num_frames_to_plot*plot_step)
            print(latents.shape)

            fig, axs = plt.subplots(3, 1, figsize=(18, 6))
            axs[0].plot( np.linspace(0, latents.shape[0]*0.02, latents.shape[0]), latents)
            axs[1].plot(np.linspace(0, commands.shape[0]*0.02, commands.shape[0]), commands)
            try:
                axs[2].imshow(bottom_frames[0])
                from matplotlib.offsetbox import TextArea, DrawingArea, OffsetImage, AnnotationBbox
                for i in range(num_frames_to_plot):
                    imagebox = OffsetImage(bottom_frames[plot_step*i], zoom=0.15)
                    ab = AnnotationBbox(imagebox, (plot_step*i*0.02, -1.7))
                    axs[0].add_artist(ab)
            except:
                print("no bottom frames")





            axs[0].set_xlim(0, 200*0.02)
            axs[0].set_ylim(-1.5, 1.5)
            axs[0].set_ylabel("latent magnitude")
            axs[0].set_xlabel("time (s)")

            axs[1].set_xlim(0, 200 * 0.02)
            axs[1].set_ylim(-0.5, 2.5)
            axs[1].set_ylabel("velocity command")
            axs[1].set_xlabel("time (s)")

            plt.savefig(filename.rsplit('.', 1)[0] + "_preview.png")

