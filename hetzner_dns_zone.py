import json

from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPClientError
from tornado.httputil import url_concat

from hetzner_dns_record import HetznerDNSRecord


class HetznerDNSZone:
    def __init__(self, api_token: str, zone_id: str):
        self.api_token: str = api_token
        self.zone_id: str = zone_id

    @classmethod
    def from_dict(cls, api_token: str, zone: dict):
        return cls(api_token, zone['id'])

    async def get_records(self) -> dict:
        try:
            response = await AsyncHTTPClient().fetch(HTTPRequest(
                url=url_concat('https://dns.hetzner.com/api/v1/records', {
                    'zone_id': self.zone_id,
                }),
                headers={
                    'Auth-API-Token': self.api_token,
                }
            ))
        except HTTPClientError as e:
            print(f'get_records failed, {e}')
            return {}
        else:
            return json.loads(response.body)['records']

    async def get_record(self, rtype: str, name: str) -> HetznerDNSRecord:
        for record in await self.get_records():
            if record['type'] == rtype and record['name'] == name:
                return HetznerDNSRecord.from_dict(self.api_token, record)
        print(f'record ({rtype} {name}) does not exist.')

    async def print_records(self):
        for record in await self.get_records():
            print(f"id: {record['id']} type: {record['type']} name: {record['name']} value: {record['value']}")
