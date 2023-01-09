#####################################################################
#####################################################################
### Pip install selenium, BeautifulSoup4, lxml, webdriver-manager ###
#####################################################################
#####################################################################


import time
import sqlite3
import logging
from datetime import datetime, timedelta
from pprint import pprint

from bs4 import BeautifulSoup as bs

from selenium import webdriver
from webdriver_manager.firefox import GeckoDriverManager
from selenium.common.exceptions import ElementClickInterceptedException, ElementNotInteractableException, \
    TimeoutException, StaleElementReferenceException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as ww

#################################################
################  Создание БД  ##################
#################################################
conn = sqlite3.connect('database/discon.db')
cur = conn.cursor()

################################################# Наполнение базы таблицей
cur.execute('''CREATE TABLE IF NOT EXISTS disconections(            
            subject TEXT,
            organisation TEXT,
            filial TEXT,
            res TEXT,
            munic TEXT,
            naspunkt TEXT,
            street TEXT,
            numofstr TEXT,
            startdate timestamp,
            starttime timestamp,
            finishdate timestamp,
            finishtime timestamp);
            ''')

cur.execute('DELETE FROM disconections;', );
conn.commit()
conn.close()

#################################### Выбор пути драйвера и сайта
# path_drv = 'geckodriver.exe'  # Для использования в linux используем "geckodriver"
auto_drv = GeckoDriverManager().install()  # Для автоматического скачивания свежего драйвера браузера firefox
url = 'https://xn----7sb7akeedqd.xn--p1ai/platform/portal/tehprisEE_disconnection'

####################################### Количество страниц регионов и настройка дат и времени
ids = list(range(85))
date_start = datetime.now()
date_start = date_start.strftime("%d.%m.%Y")
date_end = datetime.now() + timedelta(days=1)
date_end = date_end.strftime("%d.%m.%Y")

###################################### Вебдрайвер и настройки для Firefox
options = webdriver.FirefoxOptions()
options.headless = False  # True - работа в фоне False - открытие браузера
options.set_preference(
    'general.useragent.override',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.62 Safari/537.36',
)
# driver = webdriver.Firefox(executable_path=path_drv, options=options)  # Для скачанного локально драйвера браузера
driver = webdriver.Firefox(executable_path=auto_drv, options=options)
wait = ww(driver, 10)

##################################### Настройка логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='info.log', encoding='utf-8')
formatter = logging.Formatter("[%(levelname)s] - [%(asctime)s] - %(module)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

i = int(0)


################################################
###########  Заполнение запроса  ###############!
################################################
def entering_data(idt_st_tm, idt_fn_tm, id_sel, id_show):
    # вводим в фильтр начало и окончание работ
    try:
        wait.until(
            lambda d: d.find_element(By.ID, 'workplaceForm:disconnectionTabsView:DataOtklFilter_input')).send_keys(
            date_start)
        logger.info(f"Введена дата начала отключения -- {date_start}")
        time.sleep(0.5)
        wait.until(lambda d: d.find_element(By.ID, f"{idt_st_tm}_input")).send_keys(
            '00:00')
        logger.info(f"Введено время начала отключения")
        time.sleep(0.5)
        wait.until(
            lambda d: d.find_element(By.ID, "workplaceForm:disconnectionTabsView:DataRecoveryFilter_input")).send_keys(
            date_end)
        logger.info(f"Введена дата окончания отключения -- {date_end}")
        time.sleep(0.5)
        wait.until(lambda d: d.find_element(By.ID, f"{idt_fn_tm}_input")).send_keys(
            '00:00')
        logger.info(f"Введено время окончания отключения")
        time.sleep(1)
    except Exception as ex:
        logger.error(f"Ошибка_блока:'Заполнение запроса'___________{ex}")
        time.sleep(0.5)

    finally:
        logger.info(f"Начало перебора за период : {date_start} - {date_end}")
        rolling_regions(id_sel, id_show)


################################################
#############  Перебор регионов  ###############!
################################################
def rolling_regions(id_sel, id_show):
    global i
    while i in range(85):
        try:
            wait.until(lambda d: d.find_element(By.ID,
                                                f"{id_sel}_label")).click()  # by CSS selector(#workplaceForm\:disconnectionTabsView\:j_idt5746_label)
            sel_subj = wait.until(lambda d: d.find_element(By.ID, f"{id_sel}_{i}"))
            name_subj = sel_subj.get_attribute('data-label')
            sel_subj.click()
            logger.info(f"Выбран субъект {name_subj}")
            time.sleep(1)
            click = wait.until(lambda d: d.find_element(By.ID, f'{id_show}'))
            click.click()
            time.sleep(3)
            logger.info(f"Отображение информации по региону: {name_subj}")
            driver.find_element(By.CSS_SELECTOR,
                                '#workplaceForm\:disconnectionTabsView\:disconnectionReests_paginator_bottom > div > ul > li:nth-child(3)').click()
            time.sleep(1)
            if i == 0:  # Возможно потребуется доработка
                rpp_scroll = driver.find_element(By.CLASS_NAME, 'rpp-scroll')
                rpp_scroll_by = driver.find_element(By.CSS_SELECTOR,
                                                    '#workplaceForm\:disconnectionTabsView\:disconnectionReests_paginator_bottom > div:nth-child(1) > ul:nth-child(1) > li:nth-child(3)').click()

        except (ElementNotInteractableException, StaleElementReferenceException) as ex:
            logger.warning(f"Ошибка_блока:'Перебор регионов'___________{ex}")
            time.sleep(0.5)
            break

        except ElementClickInterceptedException as exep:
            logger.warning(f"Ошибка_блока:'Перебор регионов'___________{exep}")
            time.sleep(2)
            get_data(url)

        finally:
            i += 1
            logger.info(f"Переход в проверку страниц региона: {name_subj}")
            print("Перехожу в проверку страниц")
            checking_pages(id_sel, id_show, name_subj)


#################################################
####  Проверка и переход на первую страницу  ####
#################################################
def checking_pages(id_sel, id_show, name_subj):
    selected = driver.find_element(By.CSS_SELECTOR, '#workplaceForm\:disconnectionTabsView\:disconnectionReests_paginator_bottom > a:nth-child(2)')
    if selected.is_displayed():
        logger.info(f"Переход на первую страницу региона: {name_subj}")
        selected.click()
        rolling_pages(name_subj)
    else:
        logger.info(f"Первая страница региона: {name_subj}")
        rolling_pages(name_subj)


#################################################
############  Перебор по страницам  #############
#################################################
def rolling_pages(name_subj):
    try:
        label_page = driver.find_element(By.CSS_SELECTOR, "#workplaceForm\:disconnectionTabsView\:disconnectionReests_paginator_bottom > span:nth-child(4) > a:nth-child(1)")
        label_page = label_page.get_attribute("aria-label")
    except NoSuchElementException as ex:
        logger.info(f"Нет отключений в регионе: {name_subj}")
    except Exception as ex:
        logger.error(f"Неизвестная ошибка заголовка страницы: {ex}")
    else:
        while True:
            parse_data(data=driver.page_source, name_subj=name_subj)
            try:
                next = driver.find_element(By.CSS_SELECTOR, "#workplaceForm\:disconnectionTabsView\:disconnectionReests_paginator_bottom > a:nth-child(5)").click()
                time.sleep(0.5)
            except ElementNotInteractableException as ex:
                logger.warning(f"Не итерабелен переход по страницам")
                break
            except ElementClickInterceptedException as ex:
                logger.warning(f"Не прогрузился переход по страницам, пробую еще......")
                continue
            except Exception as ex:
                logger.error(f"Неизвестная ошибка перехода по страницам: {ex}")
                break


#################################################
###############  Перебор сайта  #################
#################################################
def get_data(url):
    driver.set_page_load_timeout(20)
    driver.implicitly_wait(5)
    driver.get(url=url)
    name_subj = ''
    time.sleep(3)
    data_ids = driver.page_source

    # поиск актуальных ids
    soup = bs(data_ids, 'lxml')
    idt = soup.find('span', text='Дата начала отключения').findNext('span', class_='ui-calendar hours-filter')
    idt_st_tm = idt.attrs['id']
    idt = soup.find('span', text='Дата окончания отключения').findNext('span', class_='ui-calendar hours-filter')
    idt_fn_tm = idt.attrs['id']
    idt = soup.find('div', class_="ui-g-12 ui-md-6 ui-lg-3").findNext('div')
    id_sel = idt.attrs['id']
    idt = soup.find('div', class_='ui-g-12').findNext('button',
                                                      class_="ui-button ui-widget ui-state-default ui-corner-all ui-button-text-only main-button butNormalWeight")
    id_show = idt.attrs['id']
    logger.info(f"id кнопки 'show' -- {id_show}")
    logger.info(f"id меню выбора субьекта РФ -- {id_sel}")
    logger.info(f"id поля ввода времени начала отключения -- {idt_st_tm}")
    logger.info(f"id поля ввода времени окончания отключения -- {idt_fn_tm}")
    time.sleep(3)
    entering_data(idt_st_tm, idt_fn_tm, id_sel, id_show)


def parse_data(data, name_subj):
    data = data
    name_subj = name_subj
    subjects = []
    organisations = []
    filials = []
    ress = []
    munics = []
    naspunkts = []
    streets = []
    numofstrs = []
    startdates = []
    starttimes = []
    finishdates = []
    finishtimes = []
    data_base = {"col_subj": subjects,
                 "col_org": organisations,
                 "col_fil": filials,
                 "col_res": ress,
                 "col_mun": munics,
                 "col_nasp": naspunkts,
                 "col_street": streets,
                 "col_numst": numofstrs,
                 "col_start_date": startdates,
                 "col_start_time": starttimes,
                 "col_fin_date": finishdates,
                 "col_fin_time": finishtimes}

    text_of = data
    soup = bs(text_of, 'lxml')
    text = soup.find('div', class_='ui-datatable-scrollable-body').find_all('tr')

    all_cols = []
    for row in text:
        cccc = row.find_all('td')
        all_cols.extend(cccc)

    for some in all_cols[::12]:
        organiz = some.text.strip().replace('\n', '')
        organiz = organiz.replace('"', '')
        subjects.append(name_subj)
        organisations.append(organiz)

    for some in all_cols[1::12]:
        filial = some.text.strip().replace('\n', '')
        filial = filial.replace('"', '')
        filials.append(filial)

    for some in all_cols[2::12]:
        res = some.text.strip().replace('\n', '')
        ress.append(res)

    for some in all_cols[3::12]:
        munic = some.text.strip().replace('\n', '')
        munics.append(munic)

    for some in all_cols[4::12]:
        naspunkt = some.text.strip().replace('\n', '')
        naspunkts.append(naspunkt)

    for some in all_cols[5::12]:
        street = some.text.strip().replace('\n', '')
        streets.append(street)

    for some in all_cols[6::12]:
        numofstr = some.text.strip().replace('\n', '')
        numofstrs.append(numofstr)

    for some in all_cols[7::12]:
        startdatetime = some.text.strip().replace('\n', '')
        start_date_time = startdatetime.replace(" ", '')
        start_date = start_date_time[:10]
        start_time = start_date_time[10:]
        print(start_date)
        print(start_time)
        startdates.append(start_date)
        starttimes.append(start_time)

    for some in all_cols[8::12]:
        finishdatetime = some.text.strip().replace('\n', '')
        finish_date_time = finishdatetime.replace(' ', '')
        finish_date = finish_date_time[:10]
        finish_time = finish_date_time[10:]
        finishdates.append(finish_date)
        finishtimes.append(finish_time)

    for i in range(len(data_base["col_subj"])):
        conn = sqlite3.connect('database/discon.db')
        cur = conn.cursor()
        cur.execute(f'''INSERT INTO disconections(subject,
                        organisation,
                        filial,
                        res,
                        munic,
                        naspunkt,
                        street, 
                        numofstr, 
                        startdate, 
                        starttime, 
                        finishdate, 
                        finishtime
                        )
                        VALUES('{data_base['col_subj'][i]}', 
                        '{data_base['col_org'][i]}', 
                        '{data_base['col_fil'][i]}', 
                        '{data_base['col_res'][i]}', 
                        '{data_base['col_mun'][i]}', 
                        '{data_base['col_nasp'][i]}', 
                        '{data_base['col_street'][i]}', 
                        '{data_base['col_numst'][i]}', 
                        '{data_base['col_start_date'][i]}', 
                        '{data_base['col_start_time'][i]}', 
                        '{data_base['col_fin_date'][i]}',
                        '{data_base['col_fin_time'][i]}');
                        ''')

        conn.commit()
        conn.close()


def prnt_db():
    conn = sqlite3.connect('database/discon.db')
    cur = conn.cursor()
    for row in cur.execute('SELECT * FROM disconections'):
        print(row)

    conn.close()
    driver.close()
    exit()


def main():
    logger.info(f"Начал парсинг в: {datetime.now().strftime('%d.%m.%y %H:%M')}")
    get_data(url)
    prnt_db()
    logger.info(f"Закончил парсить в: {datetime.now().strftime('%d.%m.%y %H:%M')}")


if __name__ == "__main__":
    main()
