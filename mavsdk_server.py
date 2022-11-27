#!/usr/bin/env python3

import asyncio
import socket

from mavsdk import System


async def run():

    drone = System()
    await drone.connect(system_address="udp://:14540")

    status_text_task = asyncio.ensure_future(print_status_text(drone))

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break

    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            break

    print("-- Arming")
    await drone.action.arm()

    print("-- Taking off")
    await drone.action.takeoff()

    await asyncio.sleep(10)

    done = False

    await drone.manual_control.set_manual_control_input(
        float(0),
        float(0),
        float(0.5),
        float(0)
    )
    print("-- Starting manual control")
    await drone.manual_control.start_position_control()

    server = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    server.bind(("0.0.0.0", 20001))

    print("-- UDP server up and listening")

    while not done:

        bytesAddressPair = server.recvfrom(1024)
        message = bytesAddressPair[0]
        address = bytesAddressPair[0]

        roll = float(message.split()[0])
        pitch = float(message.split()[1])
        throttle = float(message.split()[2])
        yaw = float(message.split()[3])
        done = False

        if message.split()[4] == "True":
            done = True

        #await drone.manual_control.set_manual_control_input(
        print(
            roll,
            pitch,
            throttle,
            yaw
        )
        await asyncio.sleep(0.1)

    print("-- Landing")
    await drone.action.land()

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
