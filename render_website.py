import json

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server

def get_template():
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template('template.html')
    return template


def render_page():
    json_file = 'books_data.json'
    with open(json_file, 'r', encoding='utf-8') as file:
        books_details = json.load(file)
    
    rendered_page = get_template().render(
        books=books_details,
    )
    with open('index.html', 'w', encoding='utf-8') as file:
        file.write(rendered_page)

if __name__ == '__main__':
    render_page()

    server=Server()

    server.watch('template.html', render_page)
    server.serve(root='.')
