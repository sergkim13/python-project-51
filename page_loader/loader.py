import os
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse
import logging
import logging.config
from progress.bar import IncrementalBar


def init_logger(name):
    logger = logging.getLogger(name)
    FORMAT = '%(levelname)s - %(name)s:%(lineno)s - %(message)s'
    logger.setLevel(logging.DEBUG)
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter(FORMAT))
    sh.setLevel(logging.DEBUG)
    logger.addHandler(sh)


init_logger(__name__)
logger = logging.getLogger(__name__)


def download(url, dir=os.getcwd()):
    '''
    Функция скачивает страницу и сохраняет ее содержимое
    в файл в указанной директории (по умолчанию - текущая директория).
    Имя файла генерируется по принципу:
    1) Берется адрес без схемы и расширения, если оно есть.
    2) Все символы, кроме букв и цифр, заменяются на дефис -.
    3) В конце ставится .html.
    '''
    if not os.path.exists(dir):
        raise FileNotFoundError
    if not os.access(dir, os.W_OK):
        raise PermissionError

    url = normalize_page_url(url)
    try:
        page = requests.get(url)
        page.raise_for_status()
        logger.info(f'requested url: {url}')
    except (requests.exceptions.RequestException, OSError, requests.exceptions.HTTPError):
        raise

    page_name = generate_name(url, ext='.html')
    page_path = os.path.abspath(generate_path(dir, page_name))
    if os.path.exists(page_path):
        raise FileExistsError

    logger.info(f'output path: {page_path}')
    logger.info('start downloading page')
    page_with_saved_files = get_page_with_saved_files(url, dir, page)
    with open(page_path, 'w') as file:
        logger.info('start writing final html file')
        file.write(page_with_saved_files)

    logger.info(f"Page was downloaded as \'{page_path}\'")
    return page_path


def get_page_with_saved_files(url, dir, page):
    logger.info('start saving local files')
    files_folder_name = generate_name(url, ext='_files')

    try:
        files_path = make_files_path(dir, files_folder_name)
    except FileExistsError:
        raise

    soup = BeautifulSoup(page.text, 'html.parser')
    files = get_files_in_domain(soup, url)
    download_local_files(files, files_folder_name, files_path)

    return soup.prettify()


def get_files_in_domain(soup, url):
    page_domain = get_domain(url)

    def get_files(tag):
        return (
            tag.name == 'img'
            and get_domain(normalize_file_url(tag['src'], url)) == page_domain

            or tag.name == 'link'
            and get_domain(normalize_file_url(tag['href'], url)) == page_domain

            or tag.name == 'script' and tag.has_attr('src')
            and get_domain(normalize_file_url(tag['src'], url)) == page_domain)

    tags = soup.find_all(get_files)
    for tag in tags:
        if tag.has_attr('src'):
            attr = 'src'
        else:
            attr = 'href'
        tag[attr] = normalize_file_url(tag[attr], url)
    return tags


def download_local_files(tags, files_folder_name, files_path):
    bar_width = len(tags)
    with IncrementalBar("Downloading:", max=bar_width) as bar:
        bar.suffix = "%(percent).1f%% (eta: %(eta)s)"
        for tag in tags:
            if tag.has_attr('src'):
                attr = 'src'
            else:
                attr = 'href'

            tag_url = tag[attr]
            file_relative_path = download_file(
                tag_url, files_folder_name, files_path)
            tag[attr] = file_relative_path
            bar.next()


def download_file(file_url, files_folder_name, files_path):
    images_ext = ('.JPEG', '.GIF', '.PNG', '.SVG')

    try:
        file = requests.get(file_url)
        file.raise_for_status()
    except (requests.exceptions.RequestException, OSError, requests.exceptions.HTTPError):
        raise

    file_name = generate_name(file_url)
    file_relative_path = generate_path(files_folder_name, file_name)
    file_absolute_path = generate_path(files_path, file_name)

    if file_url.upper().endswith(images_ext):
        with open(file_absolute_path, 'wb') as f:
            f.write(file.content)
        return file_relative_path

    else:
        with open(file_absolute_path, 'w') as f:
            f.write(file.text)
        return file_relative_path


def make_files_path(dir, files_folder_name):
    files_path = generate_path(dir, files_folder_name)
    os.mkdir(files_path)
    return files_path


def normalize_page_url(url):
    url_parts = list(urlparse(url))
    scheme = url_parts[0]
    if not scheme:
        url = 'https://' + url
    return url


def normalize_file_url(file_url, page_url):
    file_url_parts = list(urlparse(file_url))
    file_url_netloc = file_url_parts[1]
    if not file_url_netloc:
        page_url_parts = urlparse(page_url)
        file_url_parts[0] = page_url_parts.scheme
        file_url_parts[1] = page_url_parts.netloc
        file_url = urlunparse(file_url_parts)
    return file_url


def get_domain(url):
    netloc = urlparse(url).netloc
    return netloc


def generate_name(url, ext=''):
    if url_has_path(url):
        url, extension = os.path.splitext(url)

    if ext != '':
        extension = ext

    url_parts = list(urlparse(url))
    url_parts[0] = ''
    url = urlunparse(url_parts)

    if url.startswith('//'):
        url = url[2:]

    name = re.sub(r'[\W_]', '-', url) + extension
    return name


def url_has_path(url):
    return True if urlparse(url).path else False


def generate_path(dir, file):
    return os.path.join(dir, file)
