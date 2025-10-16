#!/usr/bin/env python3

import asyncio
import socket

from mavsdk import System


async def run():

    drone = System()
    await drone.connect(system_address="udpin://:14540")

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

    done = False
    try:

        while not done:

            bytesAddressPair = server.recvfrom(1024)
            message = bytesAddressPair[0]
            address = bytesAddressPair[0]

            roll = float(message.split()[0])
            pitch = float(message.split()[1])
            throttle = float(message.split()[2])
            yaw = float(message.split()[3])
            trans_to_fixedwing = int(message.split()[4])
            trans_to_multicopter = int(message.split()[5])
            done = False

            if message.split()[6] == b"True":
                done = True
            elif trans_to_fixedwing == 1:
                print("-- Transition to fixed wing")
                await drone.action.transition_to_fixedwing() 
            elif trans_to_multicopter == 1:
                print("-- Transition to multicopter")
                await drone.action.transition_to_multicopter()


            print(
                roll,
                pitch,
                throttle,
                yaw,
                done
            )
            await drone.manual_control.set_manual_control_input(
                roll,
                pitch,
                throttle,
                yaw
            )

        print("-- Transition to multicopter")
        await drone.action.transition_to_multicopter()

        print("-- Landing")
        await drone.action.land()

        status_text_task.cancel()

    except KeyboardInterrupt:
        print("-- Keyboard interrupt . . . exiting.")

async def print_status_text(drone):
    try:
        async for status_text in drone.telemetry.status_text():
            print(f"Status: {status_text.type}: {status_text.text}")
    except asyncio.CancelledError:
        return


if __name__ == "__main__":
    asyncio.run(run())
