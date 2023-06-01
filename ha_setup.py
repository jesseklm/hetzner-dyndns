import asyncio

from ha_host import HAHost
from hetzner_dns_record import HetznerDNSRecord


class HASetup:
    def __init__(self, hosts: dict, record: HetznerDNSRecord):
        self.hosts: list[HAHost] = []
        for host in hosts:
            self.hosts.append(HAHost(host, hosts[host]['value']))
        self.record: HetznerDNSRecord = record

    @classmethod
    async def from_config(cls, config: dict):
        self: HASetup = cls(config['ha'], HetznerDNSRecord.from_config(config))
        await self.record.get_value()
        return self

    async def run(self):
        while True:
            for host in self.hosts:
                if not await host.check_online():
                    continue
                if host.update_value != self.record.value:
                    await self.record.update(host.update_value)
                    print(f'{self.record.name} updated to {self.record.value}', flush=True)
                break
            else:
                print(f'{self.record.name} has no online candidate!', flush=True)
            await asyncio.sleep(60)
