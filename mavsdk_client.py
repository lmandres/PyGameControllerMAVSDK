#!/usr/bin/env python3

import socket
import time

import pygame


def run():

    pygame.init()
    pygame.joystick.init()

    client = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

    if pygame.joystick.get_count():

        joystick = pygame.joystick.Joystick(0)

        try:

            while True:

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        done = True

                roll = float(-joystick.get_axis(3))
                pitch = float(joystick.get_axis(2))
                throttle = float(0.5+(-(joystick.get_axis(1))/2))
                yaw = float(joystick.get_axis(0))

                button_land_left = joystick.get_button(4)
                button_land_right = joystick.get_button(5)
                done = False

                if button_land_left == 1 and button_land_right == 1:
                    done = True

                message = "{} {} {} {} {} {} {}".format(
                    roll,
                    pitch,
                    throttle,
                    yaw,
                    button_land_left,
                    button_land_right,
                    done
                )
                print(message)
                client.sendto(message.encode(), ("127.0.0.1", 20001))

                time.sleep(0.1)

        except KeyboardInterrupt:
            print("Keyboard interrupt . . . exiting.")

    pygame.joystick.quit()
    pygame.quit()


if __name__ == "__main__":
    run()
