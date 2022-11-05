import os
import secrets
import string
from abc import ABC
from pathlib import Path

import yaml

from hetzner_dns import HetznerDNS

import asyncio

import tornado.web

from hetzner_dns_record import HetznerDNSRecord


class GenerateHandler(tornado.web.RequestHandler, ABC):
    def get(self, api_token, zone_name, record_type, record_name):
        dns = HetznerDNS(api_token)
        zone = dns.get_zone(zone_name)
        record = zone.get_record(record_type, record_name)
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


class UpdateHandler(tornado.web.RequestHandler, ABC):
    def get(self, *args):
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
            record = HetznerDNSRecord.from_config(config[args[i * 2]])
            record.update(args[i * 2 + 1])
        self.write('ok')


class Dyndns2Handler(tornado.web.RequestHandler, ABC):
    def get(self):
        print(self.request.arguments)
        print(self.request.body_arguments)
        print(self.request.query_arguments)
        print(self.request.headers)


def make_app():
    reg: str = r'([\w.:]*)'
    update_url: str = f'/update/{reg}/{reg}'
    handlers: list = [
        (f'/update', Dyndns2Handler),  # ?system=dyndns&hostname={reg}&myip={reg}
        (update_url, UpdateHandler),
    ]
    for _ in range(int(os.environ.get('MAX_UPDATES_PER_GET', 2)) - 1):
        update_url += f'/{reg}/{reg}'
        handlers.append((update_url, UpdateHandler))
    if 'DISABLE_GENERATE' not in os.environ:
        handlers.append((f'/generate/{reg}/{reg}/{reg}/{reg}', GenerateHandler))
    return tornado.web.Application(handlers)


async def main():
    app = make_app()
    app.listen(8888, xheaders=True)
    shutdown_event = asyncio.Event()
    await shutdown_event.wait()


def get_config_local(filename: Path) -> dict:
    if not filename.exists():
        return {'error': 'file does not exist'}
    with open(filename, 'r') as file:
        try:
            return yaml.safe_load(file)
        except yaml.YAMLError as e:
            print(e)
            return {'error': str(e)}


if __name__ == '__main__':
    config: dict = get_config_local(Path('config.yaml'))
    asyncio.run(main())
