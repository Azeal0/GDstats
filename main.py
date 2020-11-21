from tkinter import Tk, ttk, Button, Entry
import webbrowser as wb
from os import path, remove, mkdir
from io import BytesIO
from csv import reader, writer
from gd import memory
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import cv2

exe_list = ['GeometryDash', 'DontRenameMeThxDash']
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
    global exe_list
    mem = None
    for p in exe_list:
        try:
            mem = memory.get_memory(p)
            break
        except RuntimeError:
            pass
    if not mem:
        popup('No GD process found!')
        return
    if path.exists(file_name):
        try:
            data = list(reader(open(file_name, newline='')))
        except FileNotFoundError:
            popup('Error reading file! Please delete\n     the file or choose another.')
            return
    else:
        data = []
    bg = np.full((69, 180, 3), 240, dtype=np.uint8)
    font = cv2.FONT_HERSHEY_COMPLEX
    img = cv2.putText(bg, 'Close this window', (15, 23), font, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    img = cv2.putText(img, 'to stop tracking.', (17, 53), font, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

    def write_data(save_data):
        save_data = [i for i in save_data if i != []]
        writer(open(file_name, 'w', newline='')).writerows(save_data)
    attempts = 0
    cv2.imshow('Tracking', img)
    while True:
        if not cv2.getWindowProperty('Tracking', cv2.WND_PROP_VISIBLE):
            write_data(data)
            return
        else:
            cv2.waitKey(1)
        if mem.is_dead() or mem.get_percent() >= 100:
            data.append([mem.get_percent()])
            attempts += 1
            while mem.is_dead() or mem.get_percent() >= 100:
                if not cv2.getWindowProperty('Tracking', cv2.WND_PROP_VISIBLE):
                    write_data(data)
                    return
                cv2.waitKey(100)
            if not cv2.getWindowProperty('Tracking', cv2.WND_PROP_VISIBLE):
                write_data(data)
                return


def graph(file_name, mode, rows=None):
    if path.exists(file_name):
        data = list(reader(open(file_name, newline='')))
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
    x, y = [], []
    if mode == 'show':
        try:
            for i in unique:
                count = 0
                for n in data:
                    if n[0] >= i[0]:
                        count += 1
                x.append(float(i[0]))
                y.append(int(count))
        except ValueError:
            popup('Error reading file!')
            return
    else:
        for i in unique:
            count = 0
            for n in data:
                if n[0] >= i[0]:
                    count += 1
            x.append(float(i[0]))
            y.append(int(count))
    x = sorted(x)
    y = sorted(y, reverse=True)

    plt.figure(figsize=(12, 6))
    plt.plot(x, y)
    plt.xlim((0, 100))
    plt.ylim((0, max(y)))
    plt.xlabel('Percent in Level')
    plt.ylabel('Attempts')
    tick_nums = [i for i in range(101) if i % 5 == 0]
    plt.xticks(tick_nums, [str(i) + "%" for i in tick_nums])

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
        data = list(reader(open(input_file, newline='')))
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
        frame_rows = range(len(data)+1)
    else:
        fps = 60
        counter = 1
        frame_rows = []
        for i in range(len(data)+1):
            if counter >= 1 or i == len(data):
                frame_rows.append(i)
                counter -= 1
            counter += 60/sps
    out = cv2.VideoWriter(output_file, cv2.VideoWriter_fourcc(*'mp4v'), fps, (1200, 600))
    rows = len(data)
    frame = 0
    for i in range(1, rows+1):
        if i in frame_rows:
            frame += 1
            bg = np.full((69, 180, 3), 240, dtype=np.uint8)
            font = cv2.FONT_HERSHEY_COMPLEX
            img = cv2.putText(bg, 'Exporting video...', (15, 23), font, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            completed = (frame/len(frame_rows))*135
            cv2.rectangle(img, (19, 38), (158, 52), (0, 0, 0), 1)
            cv2.rectangle(img, (21, 40), (int(completed)+21, 50), (0, 0, 0), -1)
            cv2.imshow('Rendering', img)
            cv2.waitKey(1)
            if not cv2.getWindowProperty('Rendering', cv2.WND_PROP_VISIBLE):
                out.release()
                remove(output_file)
                return
            try:
                out.write(graph(input_file, 'return', i))
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
        track(f'stats/{user_input}.csv', main_window)
        start_window()

    track_btn = Button(text='Track', command=lambda: get_track(), width=10)
    track_btn.place(x=29, y=82)

    def get_graph():
        user_input = input_field.get()
        if not path.exists(f'stats/{user_input}.csv'):
            popup('File does not exist!')
            return
        graph(f'stats/{user_input}.csv', 'show')
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
        if not path.exists(f'stats/{user_input}.csv'):
            popup('File does not exist!')
            return
        video(f'stats/{user_input}.csv', f'videos/{user_input}.mp4', sps_field.get(), main_window)
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
