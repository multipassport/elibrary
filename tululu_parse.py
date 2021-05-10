import argparse
import logging
import os
import requests
import urllib3

from bs4 import BeautifulSoup
from pathlib import Path
from pathvalidate import sanitize_filename
from requests.exceptions import HTTPError
from urllib.parse import urljoin, urlparse


def check_for_redirect(response):
    if response.history:
        raise HTTPError


def download_txt(url, filename, book_id, folder='books'):
    Path(f'./{folder}').mkdir(exist_ok=True)
    clear_filename = f'{book_id}.{sanitize_filename(filename)}'
    filepath = f'{os.path.join(folder, clear_filename)}.txt'

    payload = {'id': book_id}
    response = requests.get(url, params=payload,
        verify=False, allow_redirects=False)
    response.raise_for_status()

    with open(filepath, 'w') as file:
        file.write(response.text)
    return filepath

def download_image(url, book_id, folder='images'):
    Path(f'./{folder}').mkdir(exist_ok=True)
    filename = f'{book_id}{os.path.splitext(urlparse(url).path)[-1]}'
    filepath = os.path.join(folder, filename)

    response = requests.get(url, verify=False)
    response.raise_for_status()

    with open(filepath, 'wb') as file:
        file.write(response.content)
    return filepath


def parse_book_page(response):
    soup = BeautifulSoup(response.text, 'lxml')

    title, author = [element.strip()
        for element in soup.select_one('h1').text.split('::')]

    genres = [genre.text for genre in soup.select('span.d_book a')]

    comments = [comment.text for comment in soup.select('.texts .black')]

    image_path = soup.select_one('.bookimage img')['src']
    image_url = urljoin(response.url, image_path)

    book_info = {
        'title': title,
        'author': author,
        'genres': genres,
        'comments': comments,
        'image_url': image_url,
        }
    return book_info


def create_parser():
    parser = argparse.ArgumentParser(
        description='Скрипт, позволяющий скачивать книги из библиотеки tululu.org',
        )
    parser.add_argument(
        'start_id',
        help='Номер первой книги из списка для скачивания',
        type=int,
        )
    parser.add_argument(
        'end_id',
        help='Номер последней книги в списке для скачивания',
        type=int,
        )
    return parser


if __name__ == '__main__':
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    logging.basicConfig(filename="tululu_parse.log", filemode='w')

    download_text_url = 'https://tululu.org/txt.php'

    parser = create_parser()
    book_ids = parser.parse_args()

    for book_id in range(book_ids.start_id, book_ids.end_id + 1):
        book_url = f'https://tululu.org/b{book_id}/'
        try:
            response = requests.get(book_url, verify=False)
            response.raise_for_status()
            check_for_redirect(response)
        except HTTPError:
            error_text = f'Book {book_id} is not found'
            print(error_text, '\n')
            logging.error(error_text)
        else:
            book_info = parse_book_page(response)
            download_image(book_info['image_url'], book_id)
            download_txt(download_text_url, book_info['title'], book_id)

            print('Автор:', book_info['author'])
            print('Название:', book_info['title'])
            print('Жанр(ы):', book_info['genres'], '\n')
