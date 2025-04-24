#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Example to get the current volume from a DLNA/DMR capable TV.

Change the target variable below to point at your TV.
Use, for example, something like netdisco to discover the URL for the service.

You can run contrib/dummy_tv.py locally to emulate a TV.
"""

import asyncio
import logging

from async_upnp_client.aiohttp import AiohttpRequester
from async_upnp_client.client_factory import UpnpFactory

logging.basicConfig(level=logging.INFO)


# target = "http://192.168.178.11:49152/description.xml"
target = "http://192.168.13.240:55909/aw"


async def main():
    # create the factory
    requester = AiohttpRequester()
    factory = UpnpFactory(requester)

    # create a device
    device = await factory.async_create_device(target)
    print("Device: {}".format(device))

    # get RenderingControle-service
    service = device.service("urn:schemas-upnp-org:service:RenderingControl:1")
    print("Service: {}".format(service))

    # perform GetVolume action
    get_volume = service.action("GetVolume")
    print("Action: {}".format(get_volume))
    result = await get_volume.async_call(InstanceID=0, Channel="Master")
    print("Action result: {}".format(result))
    current_volume = result["CurrentVolume"]
    print(f"當前音量: {current_volume}%")

    # 計算新音量(限制在0-100範圍)
    volume_step = 5
    new_volume = min(max(current_volume + volume_step, 0), 100)

    # 設定新音量
    set_volume_action = service.action("SetVolume")
    result = await set_volume_action.async_call(
        InstanceID=0,
        Channel="Master",
        DesiredVolume=new_volume
    )
    print(f'Action result: {result}')
    # print(f"已調整音量至: {new_volume}%")


loop = asyncio.get_event_loop()
loop.run_until_complete(main())