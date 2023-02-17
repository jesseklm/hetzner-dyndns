import json

from tornado.httpclient import AsyncHTTPClient, HTTPClientError, HTTPRequest


class HetznerDNSRecord:
    def __init__(self, api_token: str, zone_id: str, record_id: str, rtype: str, name: str, ttl: int):
        self.api_token: str = api_token
        self.zone_id: str = zone_id
        self.record_id: str = record_id
        self.type: str = rtype
        self.name: str = name
        self.ttl: int = ttl
        self.value: str = ''

    @classmethod
    def from_dict(cls, api_token: str, record: dict):
        return cls(api_token, record['zone_id'], record['id'], record['type'], record['name'], record['ttl'])

    @classmethod
    def from_config(cls, config: dict):
        return cls(config['api_token'], config['zone_id'], config['record']['id'], config['record']['type'],
                   config['record']['name'], config['record']['ttl'])

    async def update(self, value: str):
        try:
            await AsyncHTTPClient().fetch(HTTPRequest(
                url=f'https://dns.hetzner.com/api/v1/records/{self.record_id}',
                method='PUT',
                headers={
                    'Content-Type': 'application/json',
                    'Auth-API-Token': self.api_token
                },
                body=json.dumps({
                    'name': self.name,
                    'ttl': self.ttl,
                    'type': self.type,
                    'value': value,
                    'zone_id': self.zone_id
                })
            ))
        except HTTPClientError as e:
            print(f'update failed, {e}')
        else:
            self.value = value

    async def get_value(self):
        try:
            response = await AsyncHTTPClient().fetch(HTTPRequest(
                url=f'https://dns.hetzner.com/api/v1/records/{self.record_id}',
                headers={
                    'Auth-API-Token': self.api_token,
                }
            ))
        except HTTPClientError as e:
            print(f'get failed, {e}')
        else:
            result = json.loads(response.body)['record']
            self.value: str = result['value']
