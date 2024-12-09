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

def red_button_pressed():
    print("Red Button Pressed!")
    time.sleep(3)  # Debounce: ignore further presses for 3 seconds

def yellow_button_pressed():
    print("Yellow Button Pressed!")
    time.sleep(3)  # Debounce: ignore further presses for 3 seconds

# Bind button presses to functions
red_button.when_pressed = red_button_pressed
yellow_button.when_pressed = yellow_button_pressed

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Squeaky Wheel")
font = pygame.font.Font(None, 74)
video_game_font = pygame.font.Font(pygame.font.match_font('freesansbold'), 74)
clock = pygame.time.Clock()

def display_message(text, color, blinking=False):
    """ Display a message on the screen."""
    screen.fill((0, 0, 0))
    message = font.render(text, True, color)
    message_rect = message.get_rect(center=(400, 300))
    screen.blit(message, message_rect)
    if blinking:
        arrow = font.render("\u2193", True, color)
        arrow_rect = arrow.get_rect(center=(400, 400))
        screen.blit(arrow, arrow_rect)
    pygame.display.flip()

print("Press the buttons to test them!")
pause()  # Keep the script running and listen for button presses
