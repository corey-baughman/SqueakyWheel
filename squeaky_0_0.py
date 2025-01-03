import pygame
import RPi.GPIO as GPIO
import time
from moviepy import VideoFileClip
import folium
import pandas as pd
from gpiozero import Button
from signal import pause
import threading
import gpxpy
import gpxpy.gpx
import numpy as np
import os
import webbrowser
import sys

# GPIO setup for gpiozero
red_button = Button(17, pull_up=False)  # Pull-down for red button
ok_button = Button(16, pull_up=True)  # Pull-up for OK button
reset_button = Button(6, pull_up=True)  # Pull-down for Reset button

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((1920, 1080), pygame.RESIZABLE)
pygame.display.set_caption("Squeaky Wheel")
clock = pygame.time.Clock()

stop_video_flag = threading.Event()
dataframe_lock = threading.Lock()
recorded_data = []
tracks_df = pd.DataFrame()

ok_button_active = True

VIDEO_START_TIME = pd.Timestamp("2024-11-26T22:59:36Z", tz="UTC")

# Custom debounce configuration
def debounce_button(last_press_time, debounce_delay):
    current_time = time.time()
    if current_time - last_press_time > debounce_delay:
        return current_time
    return None

last_red_button_press = 0
last_ok_button_press = 0
last_reset_button_press = 0
DEBOUNCE_DELAY = 0.3  # Seconds

def interpolate_gpx_data(gpx_data):
    points = []
    for track in gpx_data.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append({
                    "time": point.time,
                    "latitude": point.latitude,
                    "longitude": point.longitude
                })
    gpx_df = pd.DataFrame(points)
    gpx_df = gpx_df.set_index("time").sort_index()

    # Interpolate for every 0.1 second
    time_index = pd.date_range(start=gpx_df.index.min(), end=gpx_df.index.max(), freq="100ms")
    interpolated_df = gpx_df.reindex(time_index).interpolate(method="time").reset_index()
    interpolated_df.columns = ["time", "latitude", "longitude"]

    return interpolated_df

def red_button_pressed():
    global last_red_button_press
    new_time = debounce_button(last_red_button_press, DEBOUNCE_DELAY)
    if new_time:
        last_red_button_press = new_time
        elapsed_time = time.time() - video_start_time
        button_time = VIDEO_START_TIME + pd.Timedelta(seconds=elapsed_time)
        print("Red Button Pressed!")
        lat, lon = get_location_for_time(button_time)
        with dataframe_lock:
            recorded_data.append({"time": button_time, "latitude": lat, "longitude": lon})

def ok_button_pressed():
    global last_ok_button_press, ok_button_active, stop_video_flag
    if not ok_button_active:
        print("OK button is inactive until video finishes.")
        return

    new_time = debounce_button(last_ok_button_press, DEBOUNCE_DELAY)
    if new_time:
        last_ok_button_press = new_time
        ok_button_active = False  # Deactivate OK button
        print("OK Button Pressed!")
        stop_video_flag.set()  # Stop the home screen video
        home_screen_thread = threading.Thread(target=play_main_video)
        home_screen_thread.start()

def reset_to_home():
    print("Restarting the script...")
    pygame.quit()  # Quit Pygame completely
    stop_video_flag.set()  # Stop any ongoing video playback

    # Relaunch the script
    python = sys.executable
    os.execv(python, [python] + sys.argv)

def reset_button_pressed():
    global last_reset_button_press
    new_time = debounce_button(last_reset_button_press, DEBOUNCE_DELAY)
    if new_time:
        last_reset_button_press = new_time
        reset_to_home()

def play_main_video():
    play_video("DowningSt.mp4")

def play_video(filename):
    global video_start_time, ok_button_active
    clip = VideoFileClip(filename)
    video_start_time = time.time()  # Record the real start time of the video
    clip.preview()
    video_start_time = None  # Reset after video ends
    ok_button_active = True  # Reactivate OK button
    save_recorded_data()
    show_congratulations_window()

def play_home_screen():
    clip = VideoFileClip("SqueakyHomeScreen.mp4")
    while not stop_video_flag.is_set():
        clip.preview()

def save_recorded_data():
    with dataframe_lock:
        df = pd.DataFrame(recorded_data)
        df.to_csv("recorded_data.csv", index=False)
        print("Recorded data saved to recorded_data.csv")
        plot_data_on_map(df)

def plot_data_on_map(df):
    if df.empty:
        print("No data to plot.")
        return

    # Drop rows with NaN values
    df = df.dropna(subset=["latitude", "longitude"])

    # Create a map centered at the mean location
    center_lat, center_lon = df["latitude"].mean(), df["longitude"].mean()
    map_object = folium.Map(location=[center_lat, center_lon], zoom_start=15)

    # Add markers for each location
    for _, row in df.iterrows():
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=f"Time: {row['time']}",
            icon=folium.Icon(color="red", icon="info-sign"),
        ).add_to(map_object)

    # Save map to an HTML file
    map_file = "map_plot.html"
    map_object.save(map_file)
    print(f"Interactive map saved as {map_file}")

    # Open the map in a new browser tab
    map_file_path = os.path.abspath(map_file)
    webbrowser.open_new_tab(f"file://{map_file_path}")

def show_congratulations_window():
    # Calculate the number of red button presses
    num_problems = len(recorded_data)

    # Create a new Pygame window for the message
    congrats_screen = pygame.display.set_mode((1920, 1080), pygame.RESIZABLE)
    pygame.display.set_caption("Congratulations")

    font = pygame.font.Font("Retro Gaming.ttf", 40)
    message = f"Congratulations!\nInstead of being spied on,\nyou reported {num_problems} problems\nfor repair!"

    pygame.mixer.init()
    pygame.mixer.music.load("house-loop-.wav")
    pygame.mixer.music.play(loops=2)

    start_time = time.time()
    running = True
    while running:
        congrats_screen.fill((0, 0, 0))

        y_offset = 300
        for line in message.split("\n"):
            text_surface = font.render(line, True, (255, 255, 0))
            text_rect = text_surface.get_rect(center=(960, y_offset))
            congrats_screen.blit(text_surface, text_rect)
            y_offset += 100

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if time.time() - start_time > 7:
            running = False

    pygame.display.quit()
    # Music will continue playing
    threading.Thread(target=wait_for_music_and_reset).start()

def wait_for_music_and_reset():
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
    reset_to_home()

def get_location_for_time(target_time):
    target_time = target_time.round("100ms")
    closest_row = tracks_df.iloc[(tracks_df["time"] - target_time).abs().argsort()[:1]]
    if not closest_row.empty:
        return closest_row.iloc[0]["latitude"], closest_row.iloc[0]["longitude"]
    return None, None

def load_gpx_file(filepath):
    with open(filepath, "r") as gpx_file:
        gpx = gpxpy.parse(gpx_file)
        return gpx

# Load GPX data and interpolate
print("Interpolating GPX data...")
gpx_data = load_gpx_file("Tuesday_Afternoon_Research-Field_Work.gpx")
tracks_df = interpolate_gpx_data(gpx_data)
print("Interpolation complete.")

# Play the home screen video
stop_video_flag.clear()
home_screen_thread = threading.Thread(target=play_home_screen)
home_screen_thread.start()

# Bind button presses to functions
red_button.when_pressed = red_button_pressed
ok_button.when_pressed = ok_button_pressed
reset_button.when_pressed = reset_button_pressed

print("Press the buttons to test them!")
pause()  # Keep the script running and listen for button presses
