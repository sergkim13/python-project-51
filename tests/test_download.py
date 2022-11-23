from page_loader import download
import requests_mock
import tempfile
import os


expected_html_path = 'tests/fixtures/expected_page.html'
expected_html_files_path = 'ru-hexlet-io-courses_files'
mock_page_path = 'tests/fixtures/mock_page_content.txt'
mock_text = open(mock_page_path).read()
url = 'https://ru.hexlet.io/courses'


def test_download():
    with requests_mock.Mocker() as m:
        m.get(url, text=mock_text)
        with tempfile.TemporaryDirectory() as temp_dir:
            result_page_path = download(url, temp_dir)
            result_html_files_path = os.path.join(temp_dir, expected_html_files_path)
            result_page = open(result_page_path).read()
            expected_page = open(expected_html_path).read()
            assert result_page == expected_page
            assert not len(os.listdir(result_html_files_path)) == 0


def test_download_to_not_exist_dir():
    not_exist_dir = 'not_exist_dir/'
    assert download(url, not_exist_dir) == 'Указанная директория не найдена.'
