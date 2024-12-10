import pygame
import RPi.GPIO as GPIO
import time
from moviepy import VideoFileClip
import folium
import pandas as pd
from gpiozero import Button
from signal import pause
import threading
import webbrowser
import gpxpy
import gpxpy.gpx
import numpy as np

# GPIO setup for gpiozero
red_button = Button(17, pull_up=False)  # Pull-down for red button
yellow_button = Button(16, pull_up=True)  # Pull-up for yellow button

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
pygame.display.set_caption("Squeaky Wheel")
font = pygame.font.Font(None, 74)
video_game_font = pygame.font.Font(pygame.font.match_font('freesansbold'), 74)
clock = pygame.time.Clock()

stop_video_flag = threading.Event()
dataframe_lock = threading.Lock()
recorded_data = []
tracks_df = pd.DataFrame()

VIDEO_START_TIME = pd.Timestamp("2024-11-26T22:59:36Z", tz="UTC")

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
    elapsed_time = time.time() - video_start_time
    button_time = VIDEO_START_TIME + pd.Timedelta(seconds=elapsed_time)
    print("Red Button Pressed!")
    lat, lon = get_location_for_time(button_time)
    with dataframe_lock:
        recorded_data.append({"time": button_time, "latitude": lat, "longitude": lon})
    time.sleep(3)  # Debounce: ignore further presses for 3 seconds

def yellow_button_pressed():
    print("Yellow Button Pressed!")
    video_thread = threading.Thread(target=play_video, args=("DowningSt.mp4",))
    video_thread.start()
    time.sleep(3)  # Debounce: ignore further presses for 3 seconds

def play_video(filename):
    global video_start_time
    clip = VideoFileClip(filename)
    video_start_time = time.time()  # Record the real start time of the video
    clip.preview()
    video_start_time = None  # Reset after video ends
    save_recorded_data()

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

    # Open the map in a web browser
    webbrowser.open(map_file)

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

def display_message(text, color, blinking=False):
    """ Display a message on the screen."""
    screen.fill((0, 0, 0))
    message = video_game_font.render(text, True, color)
    message_rect = message.get_rect(center=(400, 300))
    screen.blit(message, message_rect)
    if blinking:
        arrow = video_game_font.render("\u2193", True, color)
        arrow_rect = arrow.get_rect(center=(400, 400))
        screen.blit(arrow, arrow_rect)
    pygame.display.flip()

def main_screen():
    display_message("Squeaky Wheel", (255, 255, 0))
    pygame.time.delay(1000)
    display_message("Press the Yellow button\n on the center console to begin", (255, 255, 0), blinking=True)

# Bind button presses to functions
red_button.when_pressed = red_button_pressed
yellow_button.when_pressed = yellow_button_pressed

main_screen()
print("Press the buttons to test them!")
pause()  # Keep the script running and listen for button presses
