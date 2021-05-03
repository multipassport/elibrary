import os
import requests
import urllib3

from bs4 import BeautifulSoup
from pathlib import Path
from pathvalidate import sanitize_filename
from requests.exceptions import HTTPError
from urllib.parse import urljoin, urlparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def check_for_redirect(response):
    if response.history:
        raise HTTPError
    return None


def download_txt(url, filename, book_id, folder='books'):
    Path(f'./{folder}').mkdir(exist_ok=True)
    clear_filename = f'{book_id}.{sanitize_filename(filename)}'
    filepath = f'{os.path.join(folder, clear_filename)}.txt'
    return filepath


def download_image(url, folder='images'):
    Path(f'./{folder}').mkdir(exist_ok=True)
    filename = os.path.split(urlparse(url).path)[-1]
    filepath = os.path.join(folder, filename)
    return filepath


def parse_book_page(response):
    soup = BeautifulSoup(response.text, 'lxml')

    title, author = [element.strip() for element in soup.find('h1').text.split('::')]

    genres = [genre.text for genre in soup.find('span', class_='d_book').find_all('a')]

    comments = [comment.find(class_='black').text for comment in soup.find_all(class_='texts')]

    image_path = soup.find(class_='bookimage').find('img')['src']
    image_url = urljoin(book_url, image_path)

    book_info = {'title': title,
        'author': author,
        'genres': genres,
        'comments': comments,
        'image_url': image_url,
    }

    return book_info



download_url = 'https://tululu.org/txt.php'


books_count = 10

for book_id in range(1, books_count + 1):
    payload = {'id': book_id}
    book_url = f'https://tululu.org/b{book_id}/'
    try:
        response = requests.get(book_url, verify=False)
        response.raise_for_status()
        check_for_redirect(response)

    except HTTPError:
        pass
    else:
        book_info = parse_book_page(response)
        print(book_info)
        
        

        
        # response = requests.get(image_url, verify=False)
        # response.raise_for_status()

        # with open(download_image(image_url), 'wb') as file:
        #     file.write(response.content)

        # file_root = download_txt(download_url, title, book_id)
        # response = requests.get(download_url, params=payload, verify=False, allow_redirects=False)
        # response.raise_for_status()
        # with open(file_root, 'w') as file:
        #     file.write(response.text)