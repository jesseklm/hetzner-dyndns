import asyncio
import traceback
from typing import Self

from dns_record import DnsRecord
from ha_host import HAHost


class HASetup:
    def __init__(self, hosts: dict, record: DnsRecord) -> None:
        self.hosts: list[HAHost] = [HAHost(host, data['value']) for host, data in hosts.items()]
        self.record = record

    @classmethod
    async def from_config(cls, config: dict) -> Self:
        self: Self = cls(config['ha'], DnsRecord.from_dict(config))
        await self.record.get_value()
        return self

    async def run(self) -> None:
        while True:
            for host in self.hosts:
                try:
                    if not await host.check_online():
                        continue
                    if host.update_value != self.record.value:
                        await self.record.update(host.update_value)
                        print(f'{self.record.name} updated to {self.record.value}', flush=True)
                except Exception as e:
                    print('ha_loop failed:', e, flush=True)
                    traceback.print_exc()
                break
            else:
                print(f'{self.record.name} has no online candidate!', flush=True)
            await asyncio.sleep(60)
