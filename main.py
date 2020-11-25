from tkinter import Tk, ttk, Button, Entry
import webbrowser as wb
import keyboard as kb
import mouse as ms
import time
from os import path, remove, mkdir
from io import BytesIO
from gd import memory
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import cv2
import pickle as pk
from scipy.signal import savgol_filter

EXE_LIST = ['GeometryDash', 'DontRenameMeThxDash']
text_field = 'Enter a save name here to start'


def popup(msg, btn='Okay'):
    window = Tk()
    window.wm_title('!')
    label = ttk.Label(window, text=msg)
    label.configure(anchor='center')
    label.pack(side='top', fill='x', pady=(20, 10), padx=(10, 10))
    b = ttk.Button(window, text=btn, command=window.destroy)
    b.pack(pady=(10, 10), padx=(10, 10))
    window.mainloop()


def track(file_name, master_window):
    master_window.destroy()
    global EXE_LIST
    mem = None
    for p in EXE_LIST:
        try:
            mem = memory.get_memory(p)
            break
        except RuntimeError:
            pass
    if not mem:
        popup('No GD process found!')
        return
    bg = np.full((69, 180, 3), 240, dtype=np.uint8)
    font = cv2.FONT_HERSHEY_COMPLEX
    img = cv2.putText(bg, 'Close this window', (15, 23), font, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    img = cv2.putText(img, 'to stop tracking.', (17, 53), font, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.imshow('Tracking', img)

    def save_data():
        try:
            to_save = pk.load(open(file_name, 'rb'))
            to_save.append([d for d in data])
        except FileNotFoundError:
            to_save = data
        pk.dump(to_save, open(file_name, 'wb'))

    data = []
    jumps = []
    jump_timers = {}
    jumping_click, jumping_up, jumping_space = False, False, False
    while mem.is_dead() or not mem.is_in_level() or mem.get_percent == 0:
        cv2.waitKey(1)
    while True:
        c_time = time.time()
        percent = mem.get_percent()
        if cv2.getWindowProperty('Tracking', cv2.WND_PROP_VISIBLE):
            cv2.waitKey(1)
        else:
            save_data()
            return
        if mem.is_dead() or percent >= 100:
            data.append([mem.get_percent(), jumps])
            jumps = []
            while mem.is_dead() or mem.get_percent() >= 100:
                if not cv2.getWindowProperty('Tracking', cv2.WND_PROP_VISIBLE):
                    save_data()
                    return
                cv2.waitKey(1)
            if not cv2.getWindowProperty('Tracking', cv2.WND_PROP_VISIBLE):
                save_data()
                return
        if mem.is_in_level():
            if not mem.is_dead() and percent < 100:
                for i in jump_timers.values():
                    if c_time - i >= 1:
                        jumps.append([list(jump_timers)[list(jump_timers.values()).index(i)], percent])
                        jump_timers = {k: v for k, v in jump_timers.items() if v != i}
                if ms.is_pressed():
                    if not jumping_click:
                        jump_timers.update({percent: c_time})
                        jumping_click = True
                else:
                    jumping_click = False
                if kb.is_pressed('up'):
                    if not jumping_up:
                        jump_timers.update({percent: c_time})
                        jumping_up = True
                else:
                    jumping_up = False
                if kb.is_pressed('space'):
                    if not jumping_space:
                        jump_timers.update({percent: c_time})
                        jumping_space = True
                else:
                    jumping_space = False
            else:
                jumps = []


def graph(file_name, mode, rows=None, cps=True):
    if path.exists(file_name):
        data = pk.load(open(file_name, 'rb'))
    else:
        popup('File does not exist!')
        return
    if not data:
        popup('File is empty!')
        return
    if rows:
        data = data[:rows]
    unique = []
    for i in data:
        if i not in unique:
            unique.append(i)
    x_atts, y_atts = [], []

    if mode == 'show':
        try:
            for i in unique:
                count = 0
                for n in data:
                    if n[0] >= i[0]:
                        count += 1
                x_atts.append(float(i[0]))
                y_atts.append(int(count))
        except ValueError:
            popup('Error reading file!')
            return
    else:
        for i in unique:
            count = 0
            for n in data:
                if n[0] >= i[0]:
                    count += 1
            x_atts.append(float(i[0]))
            y_atts.append(int(count))
    x_atts = sorted(x_atts)
    y_atts = sorted(y_atts, reverse=True)

    x_cps = []
    y_cps = []
    points = np.linspace(0, 100, 1001)
    for p in points:
        atts = 0
        clicks = 0
        for i in data:
            if i[0] > p:
                atts += 1
                for d in i[1]:
                    if d[0] < p < d[1]:
                        clicks += 1
        if atts > 0:
            x_cps.append(p)
            y_cps.append(clicks / atts)
    y_cps_smooth = savgol_filter(y_cps, 69, 7)

    fig, ax1 = plt.subplots(figsize=(12, 6))

    ax1.plot(x_atts, y_atts)
    ax1.set_title(file_name.split('/')[1].split('.')[0])
    ax1.set_xlim((0, 100))
    ax1.set_ylim((0, max(y_atts)))
    ax1.set_xlabel('Percent in Level')
    plt.ylabel('Attempts', color='tab:blue')
    tick_nums_atts = [i for i in range(101) if i % 5 == 0]
    plt.xticks(tick_nums_atts, [str(i) + "%" for i in tick_nums_atts])

    if cps:
        ax2 = ax1.twinx()
        ax2.set_yticks(np.linspace(0, 15, 6))
        ax2.set_ylabel('Average CPS', color='tab:red')
        ax2.plot(x_cps, y_cps_smooth, color='tab:red', linewidth=1)
        ax2.tick_params(axis='y', labelcolor='tab:red')
        ax2.set_ylim((0, 15))

    if mode == 'show':
        plt.show()
    elif mode == 'return':
        with BytesIO() as out:
            plt.savefig(out)
            plt.close()
            img = Image.open(out)
            img_arr = np.array(img.getdata(), dtype=np.uint8).reshape((img.size[1], img.size[0], -1))
            return cv2.cvtColor(img_arr, cv2.COLOR_RGB2BGR)


def video(input_file, output_file, sps, master_window):
    master_window.destroy()
    sps = int(sps)
    if path.exists(input_file):
        pk.load(input_file)
        if not data:
            popup('File is empty!')
            return
    else:
        popup('File does not exist!')
        return
    if path.exists(output_file):
        remove(output_file)
    if sps < 60:
        fps = int(sps)
        frame_rows = range(len(data) + 1)
    else:
        fps = 60
        counter = 1
        frame_rows = []
        for i in range(len(data) + 1):
            if counter >= 1 or i == len(data):
                frame_rows.append(i)
                counter -= 1
            counter += 60 / sps
    out = cv2.VideoWriter(output_file, cv2.VideoWriter_fourcc(*'mp4v'), fps, (1200, 600))
    rows = len(data)
    frame = 0
    for i in range(1, rows + 1):
        if i in frame_rows:
            frame += 1
            bg = np.full((69, 180, 3), 240, dtype=np.uint8)
            font = cv2.FONT_HERSHEY_COMPLEX
            img = cv2.putText(bg, 'Exporting video...', (15, 23), font, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            completed = (frame / len(frame_rows)) * 135
            cv2.rectangle(img, (19, 38), (158, 52), (0, 0, 0), 1)
            cv2.rectangle(img, (21, 40), (int(completed) + 21, 50), (0, 0, 0), -1)
            cv2.imshow('Rendering', img)
            cv2.waitKey(1)
            if not cv2.getWindowProperty('Rendering', cv2.WND_PROP_VISIBLE):
                out.release()
                remove(output_file)
                return
            try:
                out.write(graph(input_file, 'return', i), 'show', cps=False)
            except ValueError:
                out.release()
                cv2.destroyAllWindows()
                remove(output_file)
                popup('Error reading file!')
                return
    cv2.destroyAllWindows()
    out.release()


def start_window():
    main_window = Tk()
    main_window.title('GDstats')
    main_window.geometry('230x210+300+300')

    name = ttk.Label(main_window, text='Created by Azeal <3')
    name.configure(anchor='center')
    name.place(x=59, y=12)

    global text_field
    input_field = Entry(main_window, width=27)
    input_field.insert(0, text_field)
    input_field.place(x=32, y=45)

    def get_track():
        if not path.exists('stats/'):
            mkdir('stats/')
        user_input = input_field.get()
        global text_field
        text_field = user_input
        track(f'stats/{user_input}.gdst', main_window)
        start_window()

    track_btn = Button(text='Track', command=lambda: get_track(), width=10)
    track_btn.place(x=29, y=82)

    def get_graph():
        user_input = input_field.get()
        if not path.exists(f'stats/{user_input}.gdst'):
            popup('File does not exist!')
            return
        graph(f'stats/{user_input}.gdst', 'show')
        start_window()

    graph_btn = Button(text='Graph', command=lambda: get_graph(), width=10)
    graph_btn.place(x=120, y=82)

    sps_label = ttk.Label(main_window, text='@              Samples/s')
    sps_label.configure(anchor='center')
    sps_label.place(x=100, y=129)

    sps_field = Entry(main_window, width=5)
    sps_field.insert(0, '60')
    sps_field.place(x=117, y=129)

    def get_video():
        user_input = input_field.get()
        global text_field
        text_field = user_input
        if not path.exists('videos/'):
            mkdir('videos/')
        if not path.exists(f'stats/{user_input}.gdst'):
            popup('File does not exist!')
            return
        video(f'stats/{user_input}.gdst', f'videos/{user_input}.mp4', sps_field.get(), main_window)
        start_window()

    video_btn = Button(text='Video', command=lambda: get_video(), width=10)
    video_btn.place(x=17, y=126)

    yt_btn = Button(text='Tutorial', width=10)
    yt_btn.place(x=29, y=170)
    yt_btn.bind("<Button-1>", lambda e: wb.open_new('https://youtu.be/-QrOjbNQPXQ'))

    discord_btn = Button(text='Discord', width=10)
    discord_btn.place(x=120, y=170)
    discord_btn.bind("<Button-1>", lambda e: wb.open_new('https://discord.gg/7JhVJct'))

    main_window.mainloop()


start_window()
