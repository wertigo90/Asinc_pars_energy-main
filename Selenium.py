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
from selenium.common.exceptions import ElementClickInterceptedException, ElementNotInteractableException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as ww


#################################################
################  Создание БД  ##################
#################################################
conn = sqlite3.connect('discon.db')
cur = conn.cursor()

########## Наполнение базы таблицей
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

cur.execute('DELETE FROM disconections;',);
conn.commit()
conn.close()

############ Выбор пути драйвера и сайта
# path_drv = 'geckodriver.exe' #Для использования в linux используем "geckodriver"
auto_drv = GeckoDriverManager().install()#Для автоматического скачивания свежего драйвера браузера firefox
url = 'https://xn----7sb7akeedqd.xn--p1ai/platform/portal/tehprisEE_disconnection'

############ Количество страниц регионов и настройка дат и времени
ids = list(range(85))
date_start = datetime.now()
date_start = date_start.strftime("%d.%m.%Y")
date_end = datetime.now() + timedelta(days=1)
date_end = date_end.strftime("%d.%m.%Y")

########## Вебдрайвер и настройки для Firefox
options = webdriver.FirefoxOptions()
options.headless = True  #True - работа в фоне False - открытие браузера
options.set_preference(
    'general.useragent.override',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.62 Safari/537.36',
)
# driver = webdriver.Firefox(executable_path=path_drv, options=options) #Для скачанного локально драйвера браузера
driver = webdriver.Firefox(executable_path=auto_drv, options=options)
wait = ww(driver, 10)

# logging.basicConfig(
#     filename="info.log",
#     filemode='a',
#     format="%(asctime)s - %(module)s - %(levelname) - %(message)s",
#     datefmt='%H:%M:%S',
#     level=logging.DEBUG,
#     )

logger = logging.getLogger(__name__)
FORMAT = "[%(levelname)s] - [%(asctime)s] - %(module)s: %(message)s"
logging.basicConfig(filename="info.log", format=FORMAT, datefmt='%d.%m.%y %H:%M:%S')
logger.setLevel(logging.DEBUG)

#################################################
###############  Перебор сайта  #################
#################################################
def get_data(url):
    driver.set_page_load_timeout(10)
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
    idt = soup.find('div', class_='ui-g-12').findNext('button', class_="ui-button ui-widget ui-state-default ui-corner-all ui-button-text-only main-button butNormalWeight")
    id_show = idt.attrs['id']
    logger.info(f"id кнопки 'show' -- {id_show}")
    logger.info(f"id меню выбора субьекта РФ -- {id_sel}")
    logger.info(f"id поля ввода времени начала отключения -- {idt_st_tm}")
    logger.info(f"id поля ввода времени окончания отключения -- {idt_fn_tm}")


    # вводим в фильтр начало и окончание работ
    try:
        time.sleep(5)
        wait.until(
            lambda d: d.find_element(By.ID, 'workplaceForm:disconnectionTabsView:DataOtklFilter_input')).send_keys(
            date_start)
        logger.info(f"ввожу дату начала отключения -- {date_start}")
        time.sleep(0.3)
        wait.until(lambda d: d.find_element(By.ID, f"{idt_st_tm}_input")).send_keys(
            '00:00')
        logger.info(f"ввожу время начала отключения")
        time.sleep(0.3)
        wait.until(
            lambda d: d.find_element(By.ID, "workplaceForm:disconnectionTabsView:DataRecoveryFilter_input")).send_keys(
            date_end)
        logger.info(f"ввожу дату окончания отключения -- {date_end}")
        time.sleep(0.3)
        wait.until(lambda d: d.find_element(By.ID, f"{idt_fn_tm}_input")).send_keys(
            '00:00')
        logger.info(f"ввожу время окончания отключения")
        time.sleep(1)

        ####### Выбор субьекта РФ
        for i in range(85):
            try:
                wait.until(lambda d: d.find_element(By.ID, f"{id_sel}_label")).click()
                sel_subj = wait.until(lambda d: d.find_element(By.ID, f"{id_sel}_{i}"))
                name_subj = sel_subj.get_attribute('data-label')
                logger.info(f"Выбираю субъект {name_subj}")
                sel_subj.click()
                logger.info(f'Нажание на субъект')
                time.sleep(0.5)
            except ElementNotInteractableException:
                logger.warning("неудалось нажать на субъект")
                time.sleep(0.5)
                continue

            cccc = 0
            while True:
                try:
                    click = wait.until(lambda d:d.find_element(By.ID, f'{id_show}'))
                    click.click()
                    time.sleep(0.5)

                except ElementClickInterceptedException:
                    # print("_______________ERR________________")
                    # print('click show')
                    pass

                except StaleElementReferenceException:
                    # print('_________________INFO________________')
                    # print('пробую нажать кнопку показать')
                    continue

                else:
                    logger.warning("Ошибка кнопки показать")
                    break

            logger.info('нажатие кнопки показать')
            time.sleep(0.5)

            cccc = 0
            # показывать по 15
            while cccc < 5:
                try:
                    driver.find_element(By.XPATH,
                                        '//*[@id="workplaceForm:disconnectionTabsView:disconnectionReests_paginator_bottom"]/div/ul/li[3]').click()
                    time.sleep(0.5)

                except Exception as ex:
                    # print("_______________ERR________________")
                    # print('raws err = ')
                    # print(ex)
                    cccc += 1
                    time.sleep(0.5)
                    # continue
                else:
                    break

            #проверка индекса страницы
            cccc = 0
            while cccc<5:
                try:
                    pagenator = driver.find_element(By.XPATH, '//*[@id="workplaceForm:disconnectionTabsView:disconnectionReests_paginator_bottom"]/a[1]')
                    # time.sleep(1)
                    label = pagenator.get_attribute('aria-label')
                    if label != 1:
                        try:
                            pagenator.click()
                            time.sleep(0.3)
                        except ElementNotInteractableException:
                            # print("_______________ERRR______________")
                            # print("НЕТ ПАГИНАТОРА, пробую еще")
                            cccc+=1
                            continue
                        else:
                            break
                            # print("Продолжаю")
                except Exception as ex:
                    logger.error(f"Ошибка: ________ {ex}")

            try:
                page_ind = wait.until(lambda d: d.find_element(
                                        By.XPATH,
                                        '//*[@id="workplaceForm:disconnectionTabsView:disconnectionReests_paginator_bottom"]/span',
                                    ))
                page = page_ind.find_element(
                    By.CSS_SELECTOR,
                    '#workplaceForm\:disconnectionTabsView\:disconnectionReests_paginator_bottom > span > a.ui-paginator-page.ui-state-default.ui-state-active.ui-corner-all',
                    )
                num = page.get_attribute('aria-label')
                ind_str = int(num)
                print(ind_str)
                if ind_str > 0:
                    parse_data(data=driver.page_source, name_subj=name_subj)

            except Exception as ex:
                # print("_______________INFO________________")
                # print("Отсутствует элемент")
                # print(ex)
                continue

            while True:
                try:
                    while True:
                        try:
                            nexts = wait.until(lambda d: d.find_element(By.XPATH, '//*[@id="workplaceForm:disconnectionTabsView:disconnectionReests_paginator_bottom"]/a[3]'))
                            logger.info(f'Нажимаю кнопку следующей страницы')
                            if nexts:
                                try:
                                    nexts.click()
                                    logger.info(f'Нажимаю кнопку следующей страницы')
                                    time.sleep(1)
                                    parse_data(data= driver.page_source, name_subj=name_subj)
                                    time.sleep(0.5)

                                except ElementClickInterceptedException:
                                    # print("___________________ERR_______________")
                                    # print("Ошибка Клик перехвачен")
                                    continue

                                except ElementNotInteractableException:
                                    # print("_______________ERR________________")
                                    # print("Элемент не интерактивен!")
                                    break

                                except Exception as ex:
                                    # print("___________________ERR_______________")
                                    # print(ex)
                                    # print(ex)
                                    break
                                else:
                                    break
                            else:
                                logger.info("закончил перебирать страницы")
                                break

                        except ElementNotInteractableException:
                            # print("_______________ERR________________")
                            # print('Нет страниц далее')
                            # print(ex)
                            # cccc += 1
                            # continue
                            break

                except ElementNotInteractableException:
                    # print("_______________ERR________________")
                    # print("not pages")
                    cccc += 1
                    time.sleep(0.5)
                    continue
                else:
                    logger.info("Перехожу к следующему субъекту")
                    logger.info(f"Выполнено_______{round(100/85*i)}")

                    break


    except ElementNotInteractableException as ex:
        logger.error(f"Ошибка:________{ex}")


    finally:
        logger.info("Возможно закончил перебор или неожиданно прервался")
        driver.close()
        driver.quit()


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
    data_base = {"col_subj":subjects,
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
        organiz = organiz.replace('"','')
        subjects.append(name_subj)
        organisations.append(organiz)


    for some in all_cols[1::12]:
        filial = some.text.strip().replace('\n', '')
        filial = filial.replace('"','')
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
        start_date_time = startdatetime.replace(" ",'')
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
        conn = sqlite3.connect('/selen/share/discon.db')
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
    conn = sqlite3.connect('discon.db')
    cur = conn.cursor()
    for row in cur.execute('SELECT * FROM disconections'):
        print(row)

    conn.close()


def main():
    logger.info(f"Начал парсинг в: {datetime.now().strftime('%d.%m.%y %H:%M')}")
    get_data(url)
    prnt_db()
    logger.info(f"Закончил парсить в: {datetime.now().strftime('%d.%m.%y %H:%M')}")



if __name__ == "__main__":
    main()
