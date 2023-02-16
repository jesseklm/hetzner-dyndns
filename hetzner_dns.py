import json

from tornado.httpclient import AsyncHTTPClient, HTTPClientError, HTTPRequest

from hetzner_dns_zone import HetznerDNSZone


class HetznerDNS:
    def __init__(self, api_token: str):
        self.api_token: str = api_token

    async def get_zones(self) -> dict:
        try:
            response = await AsyncHTTPClient().fetch(HTTPRequest(
                url='https://dns.hetzner.com/api/v1/zones',
                headers={
                    'Auth-API-Token': self.api_token
                }
            ))
        except HTTPClientError as e:
            print(f'get_zones failed, {e}')
            return {}
        else:
            return json.loads(response.body)['zones']

    async def get_zone(self, name: str) -> HetznerDNSZone:
        for zone in await self.get_zones():
            if zone['name'] == name:
                return HetznerDNSZone.from_dict(self.api_token, zone)

    async def print_zones(self):
        for zone in await self.get_zones():
            print(f"id: {zone['id']} name: {zone['name']}")

    async def get_record(self, record_id: str):
        try:
            response = await AsyncHTTPClient().fetch(HTTPRequest(
                url=f'https://dns.hetzner.com/api/v1/records/{record_id}',
                headers={
                    'Auth-API-Token': self.api_token
                }
            ))
        except HTTPClientError as e:
            print(f'get_record failed, {e}')
        else:
            return json.loads(response.body)['record']
