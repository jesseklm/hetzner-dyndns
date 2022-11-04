import secrets
import socket
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
    def get(self, key, value):
        entry: dict = config.get(key, None)
        if entry is None:
            self.write('failed')
            return
        record = HetznerDNSRecord.from_config(entry)
        record.update(value)
        self.write('ok')


def make_app():
    return tornado.web.Application([
        (r"/update/(.*)/(.*)", UpdateHandler),
        (r"/generate/(.*)/(.*)/(.*)/(.*)", GenerateHandler),
    ])


async def main():
    app = make_app()
    server = app.listen(8888)
    server.trusted_downstream = [socket.gethostbyname('nginx')]
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
