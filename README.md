# hetzner-dyndns service

Service providing an API to update a specific DNS entry.

## API

generate config entry:

```ruby
https://YOUR_HOST/dns/generate/HETZNER_API_TOKEN/ZONE_NAME/RECORD_TYPE/RECORD_NAME
```

update record:

```ruby
https://YOUR_HOST/dns/update/KEY/NEW_IP
```

update multiple records (set `MAX_UPDATES_PER_GET` env variable, default=2):

```ruby
https://YOUR_HOST/dns/update/KEY/NEW_IP[/KEY2/VALUE2]
```

## create `config.yaml` entry

- generate config entry
- append output to `hetzner-dyndns/config.yaml`
- set `DISABLE_GENERATE=1` env variable in docker compose file
- restart service

## fritzbox configuration

- go to `Internet / Permit Access / DynDNS`
- check `Use DynDNS`
- select `User-defined`
- set `Update URL` to `https://YOUR_HOST/dns/update/<pass>/<ipaddr>` (`<ip6addr> for AAAA record`)
- set `Domain name` to `RECORD_NAME.ZONE_NAME`
- set `Username` to `ZONE_NAME`
- set `Password` to `KEY` (first line of generate output without `:`)

## opnsense ddclient configuration

- select `Custom` as `Service`
- select `DynDns2` as `Protocol`
- set `Server` to `YOUR_HOST`
- set `Username` to `ZONE_NAME`
- set `Password` to `KEY` (first line of generate output without `:`)
- untick `Wildcard`
- set `Hostname(s)` to `RECORD_NAME.ZONE_NAME`
- tick `Force SSL`

## additional configuration files

nginx config example (`site.conf` file in `nginx/config` folder), replace `YOUR_CERTPATH` and `YOUR_HOST`:

```nginx
ssl_certificate /YOUR_CERTPATH/fullchain.pem;
ssl_certificate_key /YOUR_CERTPATH/privkey.pem;

server {
    server_name YOUR_HOST;
    listen 443 ssl http2;
    listen [::]:443 ssl http2;

    location /dns/ {
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_pass http://hetzner-dyndns:8888/;
    }

    location /nic/ {
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_pass http://hetzner-dyndns:8888;
    }
}

## CATCH ALL: REDIRECT
server {
    server_name _;
    listen 80 default_server;
    listen [::]:80 default_server;
    listen 443 ssl http2 default_server;
    listen [::]:443 ssl http2 default_server;

    location / {
        return 301 https://YOUR_HOST$request_uri;
    }
}
```

docker compose example:

```yaml
services:
  nginx:
    container_name: nginx
    depends_on:
      - hetzner-dyndns
    image: nginx:mainline-alpine
    networks:
      - nginx
    ports:
      - 80:80
      - 443:443
    restart: unless-stopped
    volumes:
      - ./nginx/config:/etc/nginx/conf.d:ro

  hetzner-dyndns:
    container_name: hetzner-dyndns
    environment:
      - DISABLE_GENERATE=1 # set after config creation
      # - MAX_UPDATES_PER_GET=3 # default=2
    image: ghcr.io/jesseklm/hetzner-dyndns:master
    networks:
      - nginx
    restart: unless-stopped
    volumes:
      - ./hetzner-dyndns/config.yaml:/usr/src/app/config.yaml:ro

networks:
  nginx:
```
