import json

import requests

from hetzner_dns_record import HetznerDNSRecord


class HetznerDNSZone:
    def __init__(self, api_token: str, zone_id: str):
        self.api_token: str = api_token
        self.zone_id: str = zone_id

    @classmethod
    def from_dict(cls, api_token: str, zone: dict):
        return cls(api_token, zone['id'])

    def get_records(self) -> dict:
        # Get Records
        # GET https://dns.hetzner.com/api/v1/records

        try:
            response = requests.get(
                url="https://dns.hetzner.com/api/v1/records",
                params={
                    "zone_id": self.zone_id,
                },
                headers={
                    "Auth-API-Token": self.api_token,
                },
            )
            # print(f'Response HTTP Status Code: {response.status_code}')
            # print(f'Response HTTP Response Body: {response.content}')
            return json.loads(response.content)['records']
        except requests.exceptions.RequestException:
            print('HTTP Request failed')

    def get_record(self, rtype: str, name: str) -> HetznerDNSRecord:
        for record in self.get_records():
            if record['type'] == rtype and record['name'] == name:
                return HetznerDNSRecord.from_dict(self.api_token, record)
        print(f'record ({rtype} {name}) does not exist.')

    def print_records(self):
        for record in self.get_records():
            print(f"id: {record['id']} type: {record['type']} name: {record['name']} value: {record['value']}")
