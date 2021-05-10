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
    for book_cart in soup.find_all(class_='d_book'):
        abc = book_cart.find('a')['href']
        book_download_links = urljoin(scifi_collection_url, abc)
        yield book_download_links


if __name__ == '__main__':
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    logging.basicConfig(filename="parse_tululu_category.log", filemode='w')

    scifi_collection_url = 'https://tululu.org/l55/'
    download_text_url = 'https://tululu.org/txt.php'
    book_page_links = []
    downloaded_books_data = []
    pages_to_parse = 4
    for page_id in range(1, pages_to_parse + 1):
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
