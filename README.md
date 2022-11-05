# hetzner-dyndns service

Service providing an API to update a specific DNS entry.

## API

generate config entry:
`https://YOUR_HOST/dns/generate/HETZNER_API_TOKEN/ZONE_NAME/RECORD_TYPE/RECORD_NAME`

update record:
`https://YOUR_HOST/dns/update/KEY/NEW_IP`

## create `config.yaml` entry

- generate config entry
- append output to `hetzner-dyndns/config.yaml`
- restart service

## fritzbox configuration

- go to `Internet / Permit Access / DynDNS`
- check `Use DynDNS`
- select `User-defined`
- set `Update URL` to `https://YOUR_HOST/dns/update/<pass>/<ipaddr>` (`<ip6addr> for AAAA record`)
- set `Domain name` to `RECORD_NAME.ZONE_NAME`
- set `Username` to `ZONE_NAME`
- set `Password` to `KEY` (first line of generate output without `:`)

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
version: "3"
services:
  nginx:
    container_name: nginx
    depends_on:
      - hetzner-dyndns
    image: nginx:mainline
    networks:
      - nginx
    ports:
      - 80:80
      - 443:443
    restart: unless-stopped
    volumes:
      - ./nginx/config:/etc/nginx/conf.d:ro

  hetzner-dyndns:
    build: https://github.com/jesseklm/hetzner-dyndns.git
    container_name: hetzner-dyndns
    networks:
      - nginx
    restart: unless-stopped
    volumes:
      - ./hetzner-dyndns/config.yaml:/usr/src/app/config.yaml:ro

networks:
  nginx:
```
