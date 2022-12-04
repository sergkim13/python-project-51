import requests_mock
import tempfile
import pytest
from page_loader import download

# Тестовые данные
url1 = 'https://vk.com'

url2 = 'https://ya.ru'
url2_mock = '<img src="assets/mock.png"/>'
url2_img_src = 'https://ya.ru/assets/mock.png'


def test_exception__page_ConnectionError():
    with requests_mock.Mocker() as m:
        m.get(url1, exc=ConnectionError)
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ConnectionError):
                download(url1, temp_dir)


def test_exception_file_ConnectionError():
    with requests_mock.Mocker() as m:
        m.get(url2, text=url2_mock)
        m.get(url2_img_src, exc=ConnectionError)
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ConnectionError):
                download(url2, temp_dir)
