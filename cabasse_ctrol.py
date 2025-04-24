import asyncio
from async_upnp_client.client_factory import UpnpFactory
from async_upnp_client.aiohttp import AiohttpRequester


class CabasseMediaController:
    def __init__(self, ip: str, port: int = 53462):
        self.device_url = f"http://{ip}:{port}/aw"
        self.requester = AiohttpRequester()
        self.factory = UpnpFactory(self.requester)
        self.avt_service = None

    async def async_connect(self):
        """連接裝置並初始化AVTransport服務"""
        self.device = await self.factory.async_create_device(self.device_url)
        self.avt_service = self.device.service("urn:schemas-upnp-org:service:AVTransport:1")

        if not self.avt_service:
            raise Exception("裝置未提供AVTransport服務")

    def _get_action(self, action_name: str):
        """驗證動作可用性"""
        if not self.avt_service or not self.avt_service.action(action_name):
            raise Exception(f"不支援 {action_name} 動作")
        return self.avt_service.action(action_name)

    async def transport_control(self, action: str, **kwargs):
        """通用傳輸控制方法"""
        action_map = {
            'play': ('Play', {'Speed': '1'}),
            'pause': ('Pause', {}),
            'stop': ('Stop', {}),
            'next': ('Next', {}),
            'previous': ('Previous', {})
        }

        if action not in action_map:
            raise ValueError("不支援的動作類型")

        action_name, defaults = action_map[action]
        params = {'InstanceID': 0, **defaults, **kwargs}

        try:
            action = self._get_action(action_name)
            await action.async_call(**params)
            print(f"{action_name} 指令已成功發送")
        except Exception as e:
            print(f"控制失敗: {str(e)}")

    async def play_media(self, media_url: str, meta_data: str = ""):
        """播放指定媒體資源"""
        set_uri_action = self._get_action("SetAVTransportURI")
        await set_uri_action.async_call(
            InstanceID=0,
            CurrentURI=media_url,
            CurrentURIMetaData=meta_data
        )

        await self.transport_control('play')


# 使用範例
async def main():
    controller = CabasseMediaController("192.168.13.138")

    try:
        await controller.async_connect()

        # 基本播放控制
        await controller.transport_control('play')
        await asyncio.sleep(10)
        await controller.transport_control('pause')
        await asyncio.sleep(5)
        await controller.transport_control('play')
        await asyncio.sleep(5)
        await controller.transport_control('stop')

        # 播放指定媒體
        media_url = "http://example.com/audio.mp3"
        await controller.play_media(media_url)

        # 曲目切換
        await controller.transport_control('next')
        await asyncio.sleep(30)
        await controller.transport_control('previous')

    except Exception as e:
        print(f"發生錯誤: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
