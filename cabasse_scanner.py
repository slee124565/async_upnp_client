# cabasse_scanner.py
import asyncio
import json
from argparse import ArgumentParser
from async_upnp_client.search import SsdpSearchListener
from async_upnp_client.aiohttp import AiohttpRequester
from async_upnp_client.client_factory import UpnpFactory
from async_upnp_client.utils import CaseInsensitiveDict


class CabasseAnalyzer:
    def __init__(self):
        self.requester = AiohttpRequester()
        self.factory = UpnpFactory(self.requester)
        self.found_devices = []

    async def _parse_device(self, headers: CaseInsensitiveDict) -> None:
        """解析裝置XML描述檔"""
        try:
            location = headers.get("location", "")
            if not location:
                return

            device = await self.factory.async_create_device(location)
            manufacturer = getattr(device, "manufacturer", "").lower()

            if "cabasse" in manufacturer:
                report = {
                    "ip": headers["_host"],
                    "model": device.model_name,
                    "services": [
                        {
                            "type": service.service_type,
                            "actions": [action.name for action in service.actions.values()]
                        }
                        for service in device.services.values()
                    ],
                    "control_urls": {
                        service.service_id: service.control_url
                        for service in device.services.values()
                    }
                }
                self.found_devices.append(report)
                self._print_report(report)

        except Exception as e:
            print(f"解析錯誤: {str(e)}")

    def _print_report(self, report: dict) -> None:
        """終端機格式化輸出"""
        print(f"\n=== Cabasse裝置發現 ===")
        print(f"IP位址: {report['ip']}")
        print(f"型號: {report['model']}")
        print("\n支援服務清單:")
        for service in report["services"]:
            print(f" - {service['type']}")
            print(f"   可用動作: {', '.join(service['actions'])}")
        print("\n控制端點:")
        for service_id, url in report["control_urls"].items():
            print(f" - {service_id}: {url}")
        print("=" * 30 + "\n")


async def async_main(target_ip: str = None) -> None:
    analyzer = CabasseAnalyzer()
    source = (target_ip, 0) if target_ip else None

    # 設定SSDP監聽器
    listener = SsdpSearchListener(
        async_callback=analyzer._parse_device,
        search_target="upnp:rootdevice",
        source=source,
        target=("239.255.255.250", 1900)
    )

    await listener.async_start()
    listener.async_search()

    # 維持搜尋5秒
    await asyncio.sleep(5)
    listener.async_stop()

    if not analyzer.found_devices:
        print("未發現Cabasse品牌裝置")


if __name__ == "__main__":
    parser = ArgumentParser(description="Cabasse UPnP裝置掃描器")
    parser.add_argument("--target", help="指定掃描目標IP")
    args = parser.parse_args()

    asyncio.run(async_main(args.target))
