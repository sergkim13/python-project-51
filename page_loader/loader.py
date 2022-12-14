import os
import requests
import logging
import logging.config
from progress.bar import IncrementalBar
from page_loader.logger import init_logger
from page_loader.html_parsing import parse_html
from page_loader.tools import generate_name, generate_path, normalize_url


# Создаем логгер
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

    url = normalize_url(url)
    try:
        page = requests.get(url)
        page.raise_for_status()
    except (requests.exceptions.RequestException, OSError) as e:
        logger.debug(str(e))
        logger.warning(f"Failed to connect to {url}")
        raise

    logger.info(f'Requested url: {url}')
    logger.info(f'Output path: {os.path.abspath(dir)}')
    page_name = generate_name(url, ext='.html')
    page_path = os.path.abspath(generate_path(dir, page_name))
    logger.info(f'Output page path: {page_path}')

    if os.path.exists(page_path):
        raise FileExistsError

    files_dir = generate_name(url, ext='_files')
    files_path = generate_path(dir, files_dir)
    logger.info(f'Output files directory path: {files_path}')
    page_content, files = parse_html(url, files_dir, page)

    with open(page_path, 'w') as file:
        logger.info('Start writing html file')
        file.write(page_content)
        logger.info('Finished writing html file')

    download_files(files, files_path)
    return page_path


def download_files(files, files_path):
    if not files:
        return

    if not os.path.exists(files_path):
        logger.info(f'Creating directory for files: {files_path}')
        os.mkdir(files_path)
    else:
        raise FileExistsError

    bar_width = len(files)
    with IncrementalBar("Downloading:", max=bar_width) as bar:
        bar.suffix = "%(percent).1f%% (eta: %(eta)s)"
        for url, file_name in files:
            try:
                download_file(url, file_name, files_path)
                bar.next()
            except (requests.exceptions.RequestException, OSError) as e:
                logger.debug(str(e))
                logger.warning(
                    f"Page resource {url} wasn't downloaded"
                )
                raise


def download_file(url, file_name, files_path):

    file = requests.get(url)
    file_absolute_path = generate_path(files_path, file_name)
    with open(file_absolute_path, 'wb') as f:
        f.write(file.content)
