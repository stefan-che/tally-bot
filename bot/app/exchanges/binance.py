import requests
from colorama import Fore


async def binance_currency(base: str, quote: str, count: int = 1) -> tuple[str, bool]:
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={base.upper()}{quote.upper()}"
    data = requests.get(url).json()
    print(f'Binance: {Fore.YELLOW}',data, Fore.BLACK)
    
    if 'code' in data:
        return 'Invalid request', False
    res = None

    if count >= 1:
        res = f"{count} {base} = {round(float(data['price']) * count, 7)} {quote}"
    else:
        res = f"{base} = {float(data['price'])} {quote}"

    if res:
        return res, True
    
    return f"{data['symbol']} price is {data['price']}", True