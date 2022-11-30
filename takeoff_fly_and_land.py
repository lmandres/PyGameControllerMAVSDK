#!/usr/bin/env python3

import asyncio

from mavsdk import System
from mavsdk.telemetry import LandedState
import pygame


async def run():

    drone = System(
        mavsdk_server_address="10.0.0.197",
        port=50051
    )

    print("Making connection to drone...")
    await drone.connect(system_address="udp://10.0.0.197:14580")
    print("Connection succeeded...")

    status_text_task = asyncio.ensure_future(print_status_text(drone))

    pygame.init()
    pygame.joystick.init()

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break
        else:
            print(state)

    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            break

    print("-- Arming")
    await drone.action.arm()

    print("-- Taking off")
    await drone.action.takeoff()

    print("-- Waiting for drone to takeoff")
    async for state in drone.telemetry.landed_state():
        if state and state == LandedState.IN_AIR:
            print("-- Drone has taken off: ", state)
            break
        elif state:
            print("-- Drone state: ", state)

    done = False
    if pygame.joystick.get_count():

        joystick = pygame.joystick.Joystick(0)

        await drone.manual_control.set_manual_control_input(
            float(0),
            float(0),
            float(0.5),
            float(0)
        )
        print("-- Starting manual control")
        await drone.manual_control.start_position_control()

        while not done:

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True

            roll = float(-joystick.get_axis(4))
            pitch = float(joystick.get_axis(3))
            throttle = float(0.5+(-(joystick.get_axis(1))/2))
            yaw = float(joystick.get_axis(0))

            button_land_left = joystick.get_button(4)
            button_land_right = joystick.get_button(5)

            if button_land_left == 1 and button_land_right == 1:
                done = True

            await drone.manual_control.set_manual_control_input(
                roll,
                pitch,
                throttle,
                yaw
            )
            await asyncio.sleep(0.1)

    pygame.joystick.quit()
    pygame.quit()

    print("-- Landing")
    await drone.action.land()

    print("-- Waiting for drone to land")
    async for state in drone.telemetry.landed_state():
        if state and state == LandedState.ON_GROUND:
            print("-- Drone has landed: ", state)
            break
        elif state:
            print("-- Drone state: ", state)

    status_text_task.cancel()



async def print_status_text(drone):
    try:
        async for status_text in drone.telemetry.status_text():
            print(f"Status: {status_text.type}: {status_text.text}")
    except asyncio.CancelledError:
        return


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
