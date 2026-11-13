import requests
from colorama import Fore
from bs4 import BeautifulSoup as bs
from app.utils import visualise



async def xe_currency(base: str, quote: str = "USD", amount: int = 1) -> tuple[str, bool]:
    url = f"https://www.xe.com/currencyconverter/convert/?Amount={amount}&From={base}&To={quote}"
    content = requests.get(url).content
    soup = bs(content, "html.parser")
    
    
    exchange_rate_html = soup.find_all("p")
    exchange_rate_html2 = soup.find_all("div", class_="amount")

    visualise(exchange_rate_html, "PRICE");
    visualise(exchange_rate_html2, "PRICE2");
    return 'Invalid request', False