from icmplib import async_ping, NameLookupError


class HAHost:
    def __init__(self, hostname: str, update_value: str):
        self.hostname: str = hostname
        self.update_value: str = update_value

    async def check_online(self) -> bool:
        try:
            result = await async_ping(self.hostname, count=5, privileged=False)
        except NameLookupError:
            return False
        return result.is_alive
