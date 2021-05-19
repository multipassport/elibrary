import argparse
import json
import logging
import os
import requests
import urllib3

from bs4 import BeautifulSoup
from pathlib import Path
from requests.exceptions import HTTPError
from tululu_parse import (parse_book_page, download_image,
    download_txt, check_for_redirect)
from urllib.parse import urljoin, urlsplit, urlparse


def get_bookpages_links(url, start_page, last_page):
    tululu_url = 'https://tululu.org/'

    for page_id in range(start_page, last_page + 1):
        page_url = urljoin(url, str(page_id))
        response = requests.get(page_url, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        for book_cart in soup.select('.d_book'):
            book_path = book_cart.select_one('a')['href']
            book_page_link = urljoin(tululu_url, book_path)
            yield book_page_link


def create_parser(last_page):
    parser = argparse.ArgumentParser(
        description='Скрипт, позволяющий скачивать книги жанра'
        ' Научная фантастика из библиотеки tululu.org',
        )
    parser.add_argument(
        '-s',
        '--start_page',
        help='Номер первой страницы из коллекции,'
        ' которую Вы собираетесь скачать',
        type=int,
        default=1,
        metavar='ПЕРВАЯ СТРАНИЦА',
        )
    parser.add_argument(
        '-l',
        '--last_page',
        help='Номер последней страницы из коллекции,'
        ' которую Вы собираетесь скачать',
        type=int,
        default=last_page,
        metavar='ПОСЛЕДНЯЯ СТРАНИЦА',
        )
    parser.add_argument(
        '--book_folder',
        help='Выбор папок для скачивания книг, обложек и json-файла',
        default='books',
        metavar='КНИГИ',
        )
    parser.add_argument(
        '--image_folder',
        help='Выбор папок для скачивания книг, обложек и json-файла',
        default='images',
        metavar='КАРТИНКИ',
        )
    parser.add_argument(
        '--json_path',
        help='Выбор папок для скачивания книг, обложек и json-файла',
        nargs='+',
        default='',
        metavar='ПУТЬ К ФАЙЛУ JSON',
        )
    parser.add_argument(
        '--skip_imgs',
        help='Если указан, обложки не будут скачиваться',
        default=False,
        action='store_true',
        )
    parser.add_argument(
        '--skip_txt',
        help='Если указан, книги не будут скачиваться',
        default=False,
        action='store_true'
        )
    return parser


def fetch_last_page_number(url):
    response = requests.get(url, verify=False)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    return soup.select('.npage')[-1].text


def download_json(folder, data):
    json_filename = 'books_data.json'
    Path(f'./{folder}').mkdir(exist_ok=True)
    json_filepath = os.path.join(folder, json_filename)

    with open(json_filepath, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    logging.basicConfig(filename='parse_tululu_category.log', filemode='w')

    scifi_collection_url = 'https://tululu.org/l55/'
    download_text_url = 'https://tululu.org/txt.php'
    last_page = fetch_last_page_number(scifi_collection_url)

    parser = create_parser(last_page)
    script_arguments = parser.parse_args()
    json_folder = script_arguments.json_path

    downloaded_books_data = []

    book_page_links = get_bookpages_links(
        scifi_collection_url,
        script_arguments.start_page,
        script_arguments.last_page
        )

    for link in book_page_links:
        book_id = urlsplit(link).path.strip('/b')
        try:
            response = requests.get(link, verify=False)
            response.raise_for_status()
            check_for_redirect(response)
            book_info = parse_book_page(response)

            if not script_arguments.skip_txt:
                download_txt(download_text_url, book_info['title'], book_id,
                    folder=script_arguments.book_folder)

            if not script_arguments.skip_imgs:
                download_image(book_info['image_url'], book_id,
                    folder=script_arguments.image_folder)

            downloaded_books_data.append(book_info)
        except HTTPError:
            logging.exception(f'Book {book_id} is not found\n')

    download_json(json_folder, downloaded_books_data)
