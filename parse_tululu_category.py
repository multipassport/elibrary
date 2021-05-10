import argparse
import json
import logging
import requests
import urllib3

from bs4 import BeautifulSoup
from pathlib import Path
from requests.exceptions import HTTPError
from tululu_parse import (parse_book_page, download_image,
    download_txt, check_for_redirect)
from urllib.parse import urljoin, urlsplit, urlparse


def get_bookpages_links(response):
    soup = BeautifulSoup(response.text, 'lxml')
    tululu_url = 'https://tululu.org/'
    
    for book_cart in soup.select('.d_book'):
        book_path = book_cart.select_one('a')['href']
        book_page_link = urljoin(tululu_url, book_path)
        yield book_page_link


def create_parser():
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
        default=1
        )
    parser.add_argument(
        '-l',
        '--last_page',
        help='Номер последней страницы из коллекции,'
        ' которую Вы собираетесь скачать',
        type=int,
        default=LAST_PAGE,
        )
    return parser


def fetch_last_page_of_collection_number(url):
    response = requests.get(scifi_collection_url, verify=False)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    return soup.select('.npage')[-1].text


if __name__ == '__main__':
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    logging.basicConfig(filename='parse_tululu_category.log', filemode='w')

    scifi_collection_url = 'https://tululu.org/l55/'
    download_text_url = 'https://tululu.org/txt.php'
    LAST_PAGE = fetch_last_page_of_collection_number(scifi_collection_url)

    parser = create_parser()
    collection_pages = parser.parse_args()

    book_page_links = []
    downloaded_books_data = []

    for page_id in range(
            collection_pages.start_page, collection_pages.last_page + 1):
        page_url = urljoin(scifi_collection_url, str(page_id))
        response = requests.get(page_url, verify=False)
        response.raise_for_status()
        book_page_links.extend(get_bookpages_links(response))

    for link in book_page_links:
        book_id = urlsplit(link).path.strip('/b')
        try:
            response = requests.get(link, verify=False)
            response.raise_for_status()
            check_for_redirect(response)
        except HTTPError:
            error_text = f'Book {book_id} is not found'
            print(error_text, '\n')
            logging.error(error_text)
        else:
            book_info = parse_book_page(response)
            try:
                payload = {'id': book_id}
                response = requests.get(
                    download_text_url, verify=False, params=payload
                    )
                response.raise_for_status()
                check_for_redirect(response)
            except HTTPError:
                error_text = f'Book {book_id} is not found'
                print(error_text, '\n')
                logging.error(error_text)
            else:
                download_txt(download_text_url, book_info['title'], book_id)
                download_image(book_info['image_url'], book_id)
                downloaded_books_data.append(book_info)
                print(f'Скачивается {book_info["title"]}')
                print(link, '\n')

    with open('books_data.json', 'w', encoding='utf-8') as file:
        json.dump(downloaded_books_data, file, indent=4, ensure_ascii=False)
