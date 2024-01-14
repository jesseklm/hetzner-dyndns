import asyncio
import base64
import ipaddress
import os
import secrets
import string
from abc import ABC
from pathlib import Path

import CloudFlare
import tornado.web
import yaml
from CloudFlare.exceptions import CloudFlareAPIError

from ha_setup import HASetup
from hetzner_dns import HetznerDNS
from hetzner_dns_record import HetznerDNSRecord
from utils import get_config_local


class GenerateHandler(tornado.web.RequestHandler, ABC):
    async def get(self, api_token, zone_name, record_type, record_name):
        dns = HetznerDNS(api_token)
        zone = await dns.get_zone(zone_name)
        record = await zone.get_record(record_type, record_name)
        entry: dict = {
            ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(20)): {
                'api_token': api_token,
                'zone_id': record.zone_id,
                'record': {
                    'id': record.record_id,
                    'type': record.type,
                    'name': record.name,
                    'ttl': record.ttl
                }
            }
        }
        entry_yaml = yaml.dump(entry, default_flow_style=False, sort_keys=False)
        self.write(f'<pre>{entry_yaml}</pre>')


def update_cloudflare(config_entry: dict, value: str):
    try:
        cf = CloudFlare.CloudFlare(token=config_entry['api_token'])
        cf.zones.dns_records.put(config_entry['zone_id'], config_entry['record']['id'], data={
            'type': config_entry['record']['type'],
            'name': config_entry['record']['name'],
            'content': value
        })
    except CloudFlareAPIError as e:
        print(f'update failed, {e}', flush=True)


async def update_entry(config_entry: dict, value: str):
    if config_entry.get('type', '') == 'cloudflare':
        await asyncio.to_thread(update_cloudflare, config_entry, value)
    else:
        record = HetznerDNSRecord.from_config(config_entry)
        await record.update(value)


class UpdateHandler(tornado.web.RequestHandler, ABC):
    async def get(self, *args):
        if len(args) % 2:
            self.write('parameters odd')
            return
        if any(len(arg) == 0 for arg in args):
            self.write('zero length arg')
            return
        for i in range(int(len(args) / 2)):
            if args[i * 2] not in config:
                self.write('failed')
                return
        for i in range(int(len(args) / 2)):
            config_entry = config[args[i * 2]]
            value = args[i * 2 + 1]
            if config_entry['record']['type'] == 'AAAA' and 'ipv6suffix' in config_entry:
                full_ipv6 = ipaddress.ip_address(value).exploded
                prefix = ':'.join(full_ipv6.split(':')[:4])
                value = f"{prefix}:{config_entry['ipv6suffix']}"
            await update_entry(config_entry, value)
        self.write('ok')


class Dyndns2Handler(tornado.web.RequestHandler, ABC):
    async def get(self):
        if self.get_query_argument('system', 'dyndns') != 'dyndns':
            print('badagent', flush=True)
            return
        ip: str = self.get_query_argument('myip')
        auth: str = self.request.headers.get('Authorization', '')
        if not auth.startswith('Basic '):
            print('badauth', flush=True)
            return
        auth = auth[6:]
        auth = base64.b64decode(auth).decode()
        key: str = auth[auth.rfind(':') + 1:]
        if key not in config:
            self.write('badauth')
            return
        await update_entry(config[key], ip)
        self.write(f'good {ip}')


def make_app():
    reg: str = r'([\w.:]*)'
    update_url: str = f'/update/{reg}/{reg}'
    handlers: list = [
        (f'/nic/update', Dyndns2Handler),
        (update_url, UpdateHandler),
    ]
    for _ in range(int(os.environ.get('MAX_UPDATES_PER_GET', 2)) - 1):
        update_url += f'/{reg}/{reg}'
        handlers.append((update_url, UpdateHandler))
    if 'DISABLE_GENERATE' not in os.environ:
        handlers.append((f'/generate/{reg}/{reg}/{reg}/{reg}', GenerateHandler))
    return tornado.web.Application(handlers)


async def init_ha():
    for key in config:
        if 'ha' in config[key]:
            ha_setup: HASetup = await HASetup.from_config(config[key])
            asyncio.create_task(ha_setup.run())


async def main():
    app = make_app()
    app.listen(8888, xheaders=True)
    await init_ha()
    await asyncio.Event().wait()


if __name__ == '__main__':
    config: dict = get_config_local(Path('config.yaml'))
    asyncio.run(main())
