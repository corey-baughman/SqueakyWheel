import pygame
import RPi.GPIO as GPIO
import time
from moviepy import VideoFileClip
from matplotlib import pyplot as plt
import gpxpy
from gpiozero import Button
from signal import pause

# GPIO setup for gpiozero
red_button = Button(17, pull_up=False)  # Pull-down for red button
yellow_button = Button(16, pull_up=True)  # Pull-up for yellow button

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Squeaky Wheel")
font = pygame.font.Font(None, 74)
video_game_font = pygame.font.Font(pygame.font.match_font('freesansbold'), 74)
clock = pygame.time.Clock()

def red_button_pressed():
    print("Red Button Pressed!")
    time.sleep(3)  # Debounce: ignore further presses for 3 seconds

def yellow_button_pressed():
    print("Yellow Button Pressed!")
    play_video("DowningSt.mov")
    time.sleep(3)  # Debounce: ignore further presses for 3 seconds

def play_video(filename):
    clip = VideoFileClip(filename)
    clip.preview()

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
