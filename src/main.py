import collections
import logging
import re
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import BASE_DIR, EXPECTED_STATUS, MAIN_DOC_URL, PEP_DOC_URL
from outputs import control_output
from utils import find_tag, get_response


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, "whatsnew/")
    response = get_response(session, whats_new_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features="lxml")

    main_div = find_tag(
        soup, "section", attrs={"id": "what-s-new-in-python"}
    )

    div_with_ul = find_tag(
        main_div, "div", attrs={"class": "toctree-wrapper"}
    )

    sections_by_python = div_with_ul.find_all(
        "li", attrs={"class": "toctree-l1"}
    )

    results = [("Ссылка на статью", "Заголовок", "Редактор, Автор")]
    for section in tqdm(sections_by_python):
        version_a_tag = find_tag(section, "a")
        href = version_a_tag["href"]
        version_link = urljoin(whats_new_url, href)
        response = get_response(session, version_link)
        if response is None:
            continue
        soup = BeautifulSoup(response.text, features="lxml")
        h1 = find_tag(soup, "h1")
        dl = find_tag(soup, "dl")
        dl_text = dl.text.replace("\n", " ")

        results.append((version_link, h1.text, dl_text))

    return results


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, "lxml")
    sidebar = find_tag(soup, "div", {"class": "sphinxsidebarwrapper"})
    ul_tags = sidebar.find_all("ul")
    for ul in ul_tags:
        if "All versions" in ul.text:
            a_tags = ul.find_all("a")
            break
    else:
        raise Exception("Не найден список c версиями Python")

    results = [("Ссылка на документацию", "Версия", "Статус")]
    pattern = r"Python (?P<version>\d\.\d+) \((?P<status>.*)\)"
    for a_tag in a_tags:
        link = a_tag["href"]
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ""
        results.append((link, version, status))

    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, "download.html")
    downloads_dir = BASE_DIR / "downloads"
    downloads_dir.mkdir(exist_ok=True)

    response = get_response(session, downloads_url)
    if response is None:
        return
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "lxml")
    table = find_tag(soup, "table", {"class": "docutils"})
    a = find_tag(table, "a", {"href": re.compile(r".+pdf-a4\.zip$")})
    url = urljoin(downloads_url, a["href"])
    filename = url.split("/")[-1]
    archive_path = downloads_dir / filename

    response = session.get(url)
    try:
        with open(archive_path, "wb") as file:
            file.write(response.content)
        logging.info(f"Архив был загружен и сохранён: {archive_path}")
    except Exception:
        logging.exception(f"Ошибка при сохранении файла: {archive_path}")


def pep(session):
    pep_short = collections.namedtuple(
        "pep_short", ["number", "title", "status", "url"]
    )
    pep_detailed = collections.namedtuple(
        "pep_detailed",
        ["number", "title", "status", "url", "checked_status"],
    )
    response = get_response(session, PEP_DOC_URL)
    soup = BeautifulSoup(response.text, "lxml")
    results = [("Статус", "Количество")]
    pep_info = []
    tables = soup.find_all("table", {"class": "pep-zero-table"})
    for table in tables:
        table_body = find_tag(table, "tbody")
        table_rows = table_body.find_all("tr")
        for row in table_rows:
            href = row.find(
                lambda tag: tag.name == "a"
                and tag.get("class") == ["pep", "reference", "internal"]
                and tag.text.isdigit()
            )
            if href is None:
                continue
            number = href.text
            title = href["title"]
            status = find_tag(row, "td").text[1:]
            url = urljoin(PEP_DOC_URL, href["href"])
            pep_data = pep_short(number, title, status, url)
            if status:
                pep_info.append(pep_data)

    pep_detailed_array = []
    for pep in tqdm(pep_info):
        details = get_response(session, pep.url)
        soup = BeautifulSoup(details.text, "lxml")
        dl = find_tag(soup, "dl")
        dt = (
            dl.find(string="Status")
            .find_parent("dt")
            .find_next_sibling("dd")
            .text
        )
        pep_detailed_data = pep_detailed(*pep, dt)
        if dt not in EXPECTED_STATUS.get(pep.status, []):
            logging.warning(
                f"Статус PEP {pep.number} не соответствует ожидаемому\n"
                f"Ожидаемые статусы: "
                f"{EXPECTED_STATUS.get(pep.status, 'Unknown status')}\n"
                f"Получено: {dt}"
            )
        pep_detailed_array.append(pep_detailed_data)

    counted = collections.Counter([i[4] for i in pep_detailed_array[1::]])
    results.extend(counted.items())
    results.append(("Total", sum(counted.values())))

    return results


MODE_TO_FUNCTION = {
    "whats-new": whats_new,
    "latest-versions": latest_versions,
    "download": download,
    "pep": pep,
}


def main():
    configure_logging()
    logging.info("Парсер запущен")

    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f"Аргументы командной строки: {args}")

    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()

    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)
    if results:
        control_output(results, args)
    logging.info("Парсер завершил работу.")


if __name__ == "__main__":
    main()
