import aiohttp
import asyncio
from bs4 import BeautifulSoup
import json

# Функція для отримання інформації про цитати та авторів з однієї сторінки
async def scrape_page(session, url):
    async with session.get(url) as response:
        page_content = await response.text()
    
    soup = BeautifulSoup(page_content, 'html.parser')
    
    quotes = []
    authors = set()
    
    for quote in soup.find_all('div', class_='quote'):
        text = quote.find('span', class_='text').get_text(strip=True)
        author = quote.find('small', class_='author').get_text(strip=True)
        tags = [tag.get_text(strip=True) for tag in quote.find_all('a', class_='tag')]
        
        quotes.append({
            'tags': tags,
            'author': author,
            'quote': text
        })
        
        authors.add(author)
    
    return quotes, list(authors)

# Функція для отримання інформації про авторів на основі списку авторів
async def scrape_authors(session, author_list):
    author_data = []
    
    for author in author_list:
        author_url = f'http://quotes.toscrape.com/author/{author.replace(" ", "-")}/'
        async with session.get(author_url) as response:
            page_content = await response.text()
        
        soup = BeautifulSoup(page_content, 'html.parser')
        
        fullname_elem = soup.find('h3', class_='author-title')
        born_date_elem = soup.find('span', class_='author-born-date')
        born_location_elem = soup.find('span', class_='author-born-location')
        description_elem = soup.find('div', class_='author-description')
        
        fullname = fullname_elem.get_text(strip=True) if fullname_elem else ""
        born_date = born_date_elem.get_text(strip=True) if born_date_elem else ""
        born_location = born_location_elem.get_text(strip=True) if born_location_elem else ""
        description = description_elem.get_text(strip=True) if description_elem else ""
        
        # Перевірка на пустий рядок перед додаванням даних
        if fullname.strip() and born_date.strip() and born_location.strip() and description.strip():
            author_data.append({
                'fullname': fullname,
                'born_date': born_date,
                'born_location': born_location,
                'description': description
            })
    
    return author_data

# Функція для перевірки наявності сторінок для скрапінгу
async def has_more_pages(session, url):
    async with session.get(url) as response:
        page_content = await response.text()
    
    soup = BeautifulSoup(page_content, 'html.parser')
    next_button = soup.find('li', class_='next')
    
    return next_button is not None

# Головна функція для скрапінгу та збереження даних
async def main():
    base_url = 'http://quotes.toscrape.com/page/'

    all_quotes = []
    all_authors = set()
    
    async with aiohttp.ClientSession() as session:
        page_num = 1
        
        while True:
            page_url = f'{base_url}{page_num}/'
            has_next_page = await has_more_pages(session, page_url)
            
            if not has_next_page:
                break
            
            quotes, authors = await scrape_page(session, page_url)
            all_quotes.extend(quotes)
            all_authors.update(authors)
            page_num += 1

    # Збереження даних в JSON файл
    with open('quotes.json', 'w', encoding='utf-8') as quotes_file:
        json.dump(all_quotes, quotes_file, ensure_ascii=False, indent=2)

    async with aiohttp.ClientSession() as session:
        author_data = await scrape_authors(session, all_authors)
        with open('authors.json', 'w', encoding='utf-8') as authors_file:
            json.dump(author_data, authors_file, ensure_ascii=False, indent=2)
            
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
