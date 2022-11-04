import json

import requests


class HetznerDNSRecord:
    def __init__(self, api_token: str, zone_id: str, record_id: str, rtype: str, name: str, ttl: int):
        self.api_token: str = api_token
        self.zone_id: str = zone_id
        self.record_id: str = record_id
        self.type: str = rtype
        self.name: str = name
        self.ttl: int = ttl

    @classmethod
    def from_dict(cls, api_token: str, record: dict):
        return cls(api_token, record['zone_id'], record['id'], record['type'], record['name'], record['ttl'])

    @classmethod
    def from_config(cls, config: dict):
        return cls(config['api_token'], config['zone_id'], config['record']['id'], config['record']['type'],
                   config['record']['name'], config['record']['ttl'])

    def update(self, value: str):
        # Update Record
        # PUT https://dns.hetzner.com/api/v1/records/{RecordID}

        try:
            response = requests.put(
                url=f"https://dns.hetzner.com/api/v1/records/{self.record_id}",
                headers={
                    "Content-Type": "application/json",
                    "Auth-API-Token": self.api_token,
                },
                data=json.dumps({
                    "name": self.name,
                    "ttl": self.ttl,
                    "type": self.type,
                    "value": value,
                    "zone_id": self.zone_id
                })
            )
            # print(f'Response HTTP Status Code: {response.status_code}')
            # print(f'Response HTTP Response Body: {response.content}')
        except requests.exceptions.RequestException:
            print('HTTP Request failed')
