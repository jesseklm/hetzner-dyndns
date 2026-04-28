import asyncio
from typing import Self

import hcloud
from cloudflare import AsyncCloudflare


class DnsRecord:
    def __init__(self, handler_type: str, api_token: str, zone_id: str, id: str, name: str, type: str):
        self.handler_type = handler_type
        self.api_token = api_token
        self.zone_id = zone_id
        self.id = id
        self.name = name
        self.type = type
        self.value = ''

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(data.get('type', 'hetzner'),
                   data['api_token'],
                   data['zone_id'],
                   data['record']['id'],
                   data['record']['name'],
                   data['record']['type'])

    async def get_value(self) -> str:
        if self.handler_type == 'cloudflare':
            client = AsyncCloudflare(api_token=self.api_token)
            result = await client.dns.records.get(
                dns_record_id=self.id,
                zone_id=self.zone_id,
            )
            self.value = getattr(result, 'content', '')
        else:
            client = hcloud.Client(token=self.api_token)
            result = await asyncio.to_thread(client.zones.get_rrset,
                                             hcloud.zones.Zone(id=self.zone_id), self.name, self.type)
            self.value = ','.join(record.value for record in result.records)
        return self.value

    async def update(self, value: str):
        if self.handler_type == 'cloudflare':
            client = AsyncCloudflare(api_token=self.api_token)
            await client.dns.records.edit(
                dns_record_id=self.id,
                zone_id=self.zone_id,
                name=self.name,
                type=self.type,
                content=value,
            )
        else:
            client = hcloud.Client(token=self.api_token)
            await asyncio.to_thread(client.zones.set_rrset_records, hcloud.zones.ZoneRRSet(
                zone=hcloud.zones.Zone(id=self.zone_id),
                id=self.id,
            ), [hcloud.zones.ZoneRecord(value=value)])
        self.value = value
