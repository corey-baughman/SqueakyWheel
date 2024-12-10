import pygame
import RPi.GPIO as GPIO
import time
from moviepy import VideoFileClip
from matplotlib import pyplot as plt
import gpxpy
import gpxpy.gpx
import pandas as pd
from gpiozero import Button
from signal import pause
import threading

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

VIDEO_START_TIME = pd.Timestamp("2024-11-26T22:59:36Z", tz="UTC")

# Load GPX file
def load_gpx_file(filepath):
    with open(filepath, "r") as gpx_file:
        gpx = gpxpy.parse(gpx_file)
        return gpx

gpx_data = load_gpx_file("Tuesday_Afternoon_Research-Field_Work.gpx")

def get_location_for_time(target_time):
    for track in gpx_data.tracks:
        for segment in track.segments:
            for point in segment.points:
                if abs((point.time - target_time).total_seconds()) <= 1:  # Match to the nearest second
                    return point.latitude, point.longitude
    return None, None

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
    clip.preview()  # Display the video directly
    video_start_time = None  # Reset after video ends
    save_recorded_data()

def save_recorded_data():
    with dataframe_lock:
        df = pd.DataFrame(recorded_data)
        df.to_csv("recorded_data.csv", index=False)
        print("Recorded data saved to recorded_data.csv")

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
