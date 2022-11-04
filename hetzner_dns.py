import json

import requests

from hetzner_dns_zone import HetznerDNSZone


class HetznerDNS:
    def __init__(self, api_token: str):
        self.api_token: str = api_token

    def get_zones(self) -> dict:
        # Get Zones
        # GET https://dns.hetzner.com/api/v1/zones

        try:
            response = requests.get(
                url="https://dns.hetzner.com/api/v1/zones",
                headers={
                    "Auth-API-Token": self.api_token,
                },
            )
            # print(f'Response HTTP Status Code: {response.status_code}')
            # print(f'Response HTTP Response Body: {response.content}')
            return json.loads(response.content)['zones']
        except requests.exceptions.RequestException:
            print('HTTP Request failed')

    def get_zone(self, name: str) -> HetznerDNSZone:
        for zone in self.get_zones():
            if zone['name'] == name:
                return HetznerDNSZone.from_dict(self.api_token, zone)

    def print_zones(self):
        for zone in self.get_zones():
            print(f"id: {zone['id']} name: {zone['name']}")

    def get_record(self, record_id: str):
        # Get Record
        # GET https://dns.hetzner.com/api/v1/records/{RecordID}

        try:
            response = requests.get(
                url=f"https://dns.hetzner.com/api/v1/records/{record_id}",
                headers={
                    "Auth-API-Token": self.api_token,
                },
            )
            # print(f'Response HTTP Status Code: {response.status_code}')
            # print(f'Response HTTP Response Body: {response.content}')
            return json.loads(response.content)['record']
        except requests.exceptions.RequestException:
            print('HTTP Request failed')
