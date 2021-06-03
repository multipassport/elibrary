import json
import os

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
from more_itertools import chunked


def get_template():
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template('template.html')
    return template


def render_pages():
    json_filename = 'books_data.json'
    books_chunk_size = 8
    folder = 'pages'

    os.makedirs(folder, exist_ok=True)
    with open(json_filename, 'r', encoding='utf-8') as file:
        books_details = json.load(file)

    books_details_pages = list(chunked(books_details, books_chunk_size))
    pages_count = len(books_details_pages)
    for page_number, page in enumerate(books_details_pages, 1):
        rendered_page = get_template().render(
            books=page,
            pages_count=pages_count,
            current_page=page_number,
        )
        page_path = os.path.join(folder, f'index{page_number}.html')
        with open(page_path, 'w', encoding='utf-8') as file:
            file.write(rendered_page)


if __name__ == '__main__':
    render_pages()

    server = Server()

    server.watch('template.html', render_pages)
    server.serve(root='.')
