import asyncio
import base64
import ipaddress
import secrets
import string

import hcloud
from cloudflare import AsyncCloudflare
from nicegui import app, ui
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from config import config, write_config
from dns_record import DnsRecord
from ha_setup import HASetup

background_tasks = set()


@app.get('/dns/update/{path:path}')
async def update_handler(path: str) -> PlainTextResponse:
    args = path.split('/')
    if len(args) % 2:
        return PlainTextResponse('parameters odd')
    if any(len(arg) == 0 for arg in args):
        return PlainTextResponse('zero length arg')
    for i in range(len(args) // 2):
        if args[i * 2] not in config:
            return PlainTextResponse('failed')
    for i in range(len(args) // 2):
        config_entry = config[args[i * 2]]
        value = args[i * 2 + 1]
        if config_entry['record']['type'] == 'AAAA' and 'ipv6suffix' in config_entry:
            full_ipv6 = ipaddress.ip_address(value).exploded
            prefix = ':'.join(full_ipv6.split(':')[:4])
            value = f"{prefix}:{config_entry['ipv6suffix']}"
        await DnsRecord.from_dict(config_entry).update(value)
    return PlainTextResponse('ok')


@app.get('/nic/update')
async def dyndns2(request: Request) -> PlainTextResponse:
    if request.query_params.get('system', 'dyndns') != 'dyndns':
        print('badagent', flush=True)
        return PlainTextResponse('')
    ip = request.query_params.get('myip')
    if not ip:
        return PlainTextResponse('nohost', status_code=400)
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Basic '):
        print('badauth', flush=True)
        return PlainTextResponse('')
    auth = auth[6:]
    auth = base64.b64decode(auth).decode()
    key: str = auth[auth.rfind(':') + 1:]
    if key not in config:
        return PlainTextResponse('badauth')
    await DnsRecord.from_dict(config[key]).update(ip)
    return PlainTextResponse(f'good {ip}')


@ui.refreshable
async def config_table() -> None:
    columns = [
        {'name': 'key', 'label': 'key', 'field': 'key'},
        {'name': 'type', 'label': 'type', 'field': 'type'},
        {'name': 'api_token', 'label': 'api_token', 'field': 'api_token'},
        {'name': 'zone_id', 'label': 'zone_id', 'field': 'zone_id'},
        {'name': 'record_id', 'label': 'record_id', 'field': 'record_id'},
        {'name': 'record_type', 'label': 'record_type', 'field': 'record_type'},
        {'name': 'record_name', 'label': 'record_name', 'field': 'record_name'},
    ]
    rows = []
    for key, value in config.items():
        rows.append({
            'key': key,
            'type': value.get('type', 'hetzner'),
            'api_token': value['api_token'],
            'zone_id': value['zone_id'],
            'record_id': value['record']['id'],
            'record_type': value['record']['type'],
            'record_name': value['record']['name'],
        })
    table = ui.table(columns=columns, rows=rows, row_key='key')
    with table.add_slot('top-right'):
        def add_key():
            with ui.dialog(value=True) as dialog, ui.card():
                type_select = ui.select(options=['cloudflare', 'hetzner'], label='type')
                api_token = ui.select(options=[], label='api_token')

                async def set_api_tokens():
                    api_token.set_options({value['api_token']: value['api_token'] for key, value in config.items() if
                                           value.get('type', 'hetzner') == type_select.value})
                    api_token.value = next(iter(api_token.options))
                    zone_id_select.clear()
                    record_select.clear()

                type_select.on_value_change(set_api_tokens)
                # type_select.value = next(iter(type_select.options))
                type_select.value = 'hetzner'
                zone_id_select = ui.select(options=[], label='zone_id')

                async def set_zone_ids():
                    zone_id_select.props('loading')
                    zones = {}
                    if type_select.value == 'cloudflare':
                        client = AsyncCloudflare(api_token=api_token.value)
                        async for zone in client.zones.list():
                            zones[zone.id] = zone.name
                    elif type_select.value == 'hetzner':
                        client = hcloud.Client(token=api_token.value)
                        for zone in await asyncio.to_thread(client.zones.get_all):
                            zones[zone.id] = zone.name
                    zone_id_select.props(remove='loading')
                    if not zones:
                        return
                    zone_id_select.set_options(zones)
                    zone_id_select.value = next(iter(zone_id_select.options))

                api_token.on_value_change(set_zone_ids)
                record_select = ui.select(options=[], label='record_id')
                full_records = {}

                async def set_record_ids():
                    record_select.props('loading')
                    records = {}
                    if type_select.value == 'cloudflare':
                        client = AsyncCloudflare(api_token=api_token.value)
                        async for record in client.dns.records.list(zone_id=zone_id_select.value):
                            records[record.id] = f'{record.type}: {record.name}'
                            full_records[record.id] = record
                    elif type_select.value == 'hetzner':
                        client = hcloud.Client(token=api_token.value)
                        for record in await asyncio.to_thread(client.zones.get_rrset_all,
                                                              hcloud.zones.Zone(id=zone_id_select.value)):
                            records[record.id] = f'{record.type}: {record.name}'
                            full_records[record.id] = record
                    record_select.props(remove='loading')
                    if not records:
                        return
                    record_select.set_options(records)
                    record_select.value = next(iter(record_select.options))

                zone_id_select.on_value_change(set_record_ids)

                with ui.row():
                    async def update_row() -> None:
                        secret_key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(20))
                        config[secret_key] = {
                            'type': type_select.value,
                            'api_token': api_token.value,
                            'zone_id': zone_id_select.value,
                            'record': {
                                'id': record_select.value,
                                'type': full_records[record_select.value].type,
                                'name': full_records[record_select.value].name,
                            }
                        }
                        await asyncio.to_thread(write_config)
                        ui.timer(0, config_table.refresh, once=True)
                        dialog.close()

                    ui.button('Save', on_click=update_row)
                    ui.button('Abort', on_click=dialog.close)

        ui.button(icon='add', on_click=add_key).props('flat dense')
        ui.button(icon='refresh', on_click=config_table.refresh).props('flat dense')


@ui.page('/', title='Home')
async def home() -> None:
    with ui.header(fixed=False).props('flat dense').classes('items-center justify-between p-1'):
        with ui.row():
            ui.button('Home', on_click=lambda: ui.navigate.to('/'), icon='home').props('flat color=white no-caps')
        with ui.row():
            with ui.dropdown_button('root', auto_close=True).props('flat color=white no-caps'):
                ui.item('Logout', on_click=lambda: ui.navigate.to('/logout'))
    with ui.row().classes('w-full justify-center'):
        with ui.card().tight():
            await config_table()


async def init_ha() -> None:
    for key, value in config.items():
        if 'ha' in value:
            ha_setup: HASetup = await HASetup.from_config(value)
            task = asyncio.create_task(ha_setup.run())
            background_tasks.add(task)
            task.add_done_callback(background_tasks.discard)


if __name__ in {"__main__", "__mp_main__"}:
    app.colors(primary='#c95e00')
    app.on_startup(init_ha)
    ui.run(show=False, reload=False, dark=True, port=8888)
