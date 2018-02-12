from urllib import *
from urllib.parse import urlparse, urljoin
from urllib.request import urlopen
import urllib.request
import requests
from io import BytesIO

from bs4 import BeautifulSoup

import time, re, collections, shutil, os, sys, zipfile, xlrd, threading
from datetime import date, datetime, timedelta
from dateutil.relativedelta import *

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.chrome.options import Options

from selenium.webdriver.firefox.options import Options

# months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
months_abbr = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

months = {
    'January': '01', 'February': '02', 'March': '03', 'April': '04', 'May': '05',
    'June': '06', 'July': '07', 'August': '08', 'September': '09',
    'October': '10', 'November': '11', 'December': '12',
    'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05',
    'Jun': '06', 'Jul': '07', 'Aug': '08', 'Sep': '09',
    'Oct': '10', 'Nov': '11', 'Dec': '12',
}

def changeDate(str):
    date_tmp = str.split('/')
    date_tmp = [date_tmp[1], date_tmp[2], date_tmp[0]]
    return '/'.join(date_tmp)

def convertDate(str):
    date_tmp = str.split('/')
    month = months_abbr[int(date_tmp[0])-1]
    day = "{:02d}".format(int(date_tmp[1]))
    year = "{:04d}".format(int(date_tmp[2]))
    return "{} {}, {}".format(month, day, year)

def invertDate1(str):
    regex = r"([a-zA-Z]+)[ ]+([\d]+)[, ]+([\d]+)"
    match = re.findall(regex, str)
    match = list(match[0])
    match[0] = months[match[0]]

    return "/".join(match)

def invertDate2(str):
    if "ago" in str:
        try:
            regex = r"([\d]+)[ ]+hour[s ]+ago"
            match = re.findall(regex, str)
            match = list(match[0])
            curDate = datetime.now() - timedelta(hours=int(match[0]))
        except:
            regex = r"([\d]+)[ ]+min[s ]+ago"
            match = re.findall(regex, str)
            match = list(match[0])
            curDate = datetime.now() - timedelta(minutes=int(match[0]))

        curDateStr = curDate.date().__str__().split('-')

        return "/".join([curDateStr[1], curDateStr[2], curDateStr[0]])
    else:
        regex = r"([a-zA-Z]+)[ ]+([\d]+)"
        match = re.findall(regex, str)
        match = list(match[0])
        match[0] = months[match[0]]
        year = datetime.now().year.__str__()
        return "/".join([match[0], match[1], year])

def download(url, num_retries=3):
    """Download function that also retries 5XX errors"""
    try:
        # headers = {
        #     'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}


        headers = {'User-agent': 'your bot 0.1'}
        result = requests.get(url, headers=headers, stream=True)
        html = result.content.decode()

    except urllib.error.URLError as e:
        print('Download error:', e.reason)
        html = None
        if num_retries > 0:
            if hasattr(e, 'code') and 500 <= e.code < 600:
                # retry 5XX HTTP errors
                html = download(url, num_retries - 1)
    except:
        html = None
    return html

def takeElement(elem, index):
    return elem[index]

class zip_downloader():
    def __init__(self, url, dest):
        self.url = url
        self.dest = dest

    def startDownloading(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
        request = requests.get(self.url, headers=headers, stream=True)
        file = zipfile.ZipFile(BytesIO(request.content))
        for name in file.namelist():
            file.extract(name, self.dest)

class FDA_scraper():
    def __init__(self):
        self.url = 'http://www.fda.gov/Safety/MedWatch/default.htm'
        self.total_data = {}

    def __str__(self):
        return 'FDA'

    def doProcess(self):
        self.startScraping()
        # db = db_writer('FDA', self.total_data)
        # db.create_table()
        # db.store_data()

        print(str(self) + " completed.")

    def startScraping(self):
        links = []
        titles = []
        descs = []
        dates = []

        html = download(self.url)
        # print('~~~~~~~~~~~~ FDA scraper ~~~~~~~~~~~~~~~~~~~~')
        # print(html)
        soup = BeautifulSoup(html, 'html.parser')

        panel = soup.select_one("div.panel-body")
        rows = panel.select("ul > li")

        for row in rows:
            link = urljoin(self.url, row.select_one("a").get('href'))
            title = row.select_one("linktitle").text.strip()
            desc = row.select_one("desc").text.strip()

            try:
                regex = r"[pP]osted ([\d]+)/([\d]+)/([\d]+)"
                match = re.findall(regex, desc)
            except:
                regex = r"Updated ([\d]+)/([\d]+)/([\d]+)"
                match = re.findall(regex, desc)

            match = list(match[0])
            date = "/".join(match)
            date = convertDate(date)

            links.append(link)
            titles.append(title)
            descs.append(desc)
            dates.append(date)

        self.total_data['_LINK'] = links
        self.total_data['_TITLE'] = titles
        self.total_data['_DESC'] = descs
        self.total_data['_DATE'] = dates

class Press_scraper():
    def __init__(self):
        self.url = 'https://www.fda.gov/NewsEvents/Newsroom/PressAnnouncements/default.htm'
        self.total_data = {}

    def __str__(self):
        return 'PRESS'

    def doProcess(self):
        self.startScraping()
        # db = db_writer('PRESS', self.total_data)
        # db.create_table()
        # db.store_data()

        print(str(self) + " completed.")

    def startScraping(self):
        links = []
        descs = []
        dates = []

        html = download(self.url)
        # print('~~~~~~~~~~~~ Press scraper ~~~~~~~~~~~~~~~~~~~~')
        # print(html)
        soup = BeautifulSoup(html, 'html.parser')

        rows = soup.select("div.panel-body > ul > li")

        for row in rows:
            link = urljoin(self.url, row.select_one("a").get('href'))
            date, desc = row.text.strip().split(" - ")

            date = invertDate1(date)
            date = convertDate(date)

            links.append(link)
            descs.append(desc)
            dates.append(date)

        self.total_data['_LINK'] = links
        self.total_data['_DESC'] = descs
        self.total_data['_DATE'] = dates

class Drug_scraper():
    def __init__(self):
        self.url = 'https://www.fda.gov/Drugs/DrugSafety/DrugRecalls/default.htm'
        self.total_data = {}

    def __str__(self):
        return 'DRUG'

    def doProcess(self):
        self.startScraping()
        # db = db_writer('DRUG', self.total_data)
        # db.create_table()
        # db.store_data()

        print(str(self) + " completed.")

    def startScraping(self):
        links = []
        dates = []
        brands = []
        descs = []
        problems = []
        companies = []

        html = download(self.url)
        # print('~~~~~~~~~~~~ Drug scraper ~~~~~~~~~~~~~~~~~~~~')
        # print(html)
        soup = BeautifulSoup(html, 'html.parser')

        rows = soup.select("tbody > tr")

        for row in rows:
            cols = row.select('td')
            date = cols[0].text
            date = convertDate(date)
            brand = cols[1].text.strip()
            link = urljoin(self.url, cols[1].select_one('a').get('href'))
            desc = cols[2].text.strip()
            problem = cols[3].text.strip()
            company = cols[4].text.strip()

            dates.append(date)
            brands.append(brand)
            links.append(link)
            descs.append(desc)
            problems.append(problem)
            companies.append(company)

        self.total_data['_DATE'] = dates
        self.total_data['_BRAND'] = brands
        self.total_data['_LINK'] = links
        self.total_data['_DESC'] = descs
        self.total_data['_PROBLEM'] = problems
        self.total_data['COMPANY'] = companies

class Maude_scraper():
    def __init__(self):
        self.url = 'https://www.fda.gov/medicaldevices/deviceregulationandguidance/postmarketrequirements/reportingadverseevents/ucm127891.htm'
        self.zip_name = 'foidevadd.zip'
        self.txt_name = "foidevadd.txt"
        self.total_data = {}

    def __str__(self):
        return 'MAUDE'

    def doProcess(self):
        self.startScraping()
        # db = db_writer('MAUDE', self.total_data)
        # db.create_table()
        # db.store_data()

        print(str(self) + " completed.")

    def startScraping(self):
        dates = []
        companies = []
        brands = []
        generics = []
        keys = []

        ''' Getting url of zip file '''
        html = download(self.url)

        # print('~~~~~~~~~~~~ Maude scraper ~~~~~~~~~~~~~~~~~~~~')
        # print(html)

        soup = BeautifulSoup(html, 'html.parser')
        rows = soup.select('tbody > tr')
        for row in rows:
            col = row.select_one('td')
            if self.zip_name in col.text:
                self.zip_url = col.select_one('a').get('href')
                break

        ''' Downloading zip file and unzipping it '''
        self.dest = os.getcwd() + "\\Data"
        app = zip_downloader(self.zip_url, self.dest)
        app.startDownloading()

        ''' Reading all data '''
        companies_nms = []
        try:
            input_xls = xlrd.open_workbook('Data/Scraper Company  Names.xls')
            sheet = input_xls.sheet_by_index(0)
            for rx in range(sheet.nrows):
                if sheet.row(rx)[0].value != '' and sheet.row(rx)[0].value != 'Company Name':
                    companies_nms.append(sheet.row(rx)[0].value)

        except:
            pass

        txt_file = open(self.dest + "\\" + self.txt_name, 'r')
        rows = txt_file.read().split('\n')

        rows_ex = []
        for row in rows:
            if row is not '':
                rows_ex.append(row.split('|'))

        data_ex = rows_ex[1:]

        ''' Filtering data '''
        for company in companies_nms:
            for i, row in enumerate(data_ex):
                search_words = company.split(' ')
                manufacturer_d_address = row[8]

                for i in range(len(search_words)):
                    search_word = ' '.join(search_words[:i + 1])
                    stop_words = ['.', ',', ';', '(', ')', '&', '  ']

                    for stop_word in stop_words:
                        while (stop_word in manufacturer_d_address):
                            manufacturer_d_address = manufacturer_d_address.replace(stop_word, ' ')

                    if search_word in manufacturer_d_address.split(' '):
                        date = row[5]
                        date = convertDate(date)

                        dates.append(date)
                        companies.append(row[8])
                        brands.append(row[6])
                        generics.append(row[7])
                        keys.append(row[0])

                        break

        self.total_data['_DATE'] = dates
        self.total_data['_COMPANY'] = companies
        self.total_data['_BRAND'] = brands
        self.total_data['_GENERIC'] = generics
        self.total_data['_KEY'] = keys

        # for v in zip(*list(self.total_data.values())):
        #     print(v)

''' Palmetto '''
class CMS_scraper1():
    def __init__(self):
        self.url = "https://www.cms.gov/medicare-coverage-database/reports/draft-lcd-status-report.aspx?name=373*1%7C374*1%7C378*1%7C375*1%7C379*1%7C376*1%7C380*1%7C377*1%7C381*1&bc=AQAAAgAAAAAAAA%3D%3D&#ResultAnchor"
        self.total_data = {}

    def __str__(self):
        return 'CMS1'

    def doProcess(self):
        self.startScraping()
        # db = db_writer('CMS', self.total_data)
        # db.create_table()
        # db.store_data()

        print(str(self) + " completed.")

    def startScraping(self):
        lcd_ids = []
        lcd_titles = []
        contractor_names = []
        statuss = []
        start_dates = []
        end_dates = []
        release_dates = []
        links = []

        html = download(self.url)
        soup = BeautifulSoup(html, 'html.parser')

        rows = soup.select_one(
            "table#ctl00_ctl00_ctl00_CMSGMainContentPlaceHolder_ToolContentPlaceHolder_MCDContentPlaceHolder_DraftLCDReport1_LCDGridView").find_all(
            "tr")

        for i, row in enumerate(rows):
            if i in [0, 1, 2, len(rows) - 2, len(rows) - 1]:
                continue

            lcd_id = row.find("th").text.strip()
            cols = row.find_all("td")
            lcd_title = cols[0].text.strip()
            contractor_name = cols[1].text.strip()
            status = cols[2].text.replace('&nbsp', '').strip()
            try:
                start_date = cols[3].text.replace('&nbsp', '').strip()
                start_date = convertDate(start_date)
            except:
                start_date = ''

            try:
                end_date = cols[4].text.replace('&nbsp', '').strip()
                end_date = convertDate(end_date)
            except:
                end_date = ''

            try:
                release_date = cols[5].text.replace('&nbsp', '').strip()
                release_date = convertDate(release_date)
            except:
                release_date = ''

            lcd_ids.append(lcd_id)
            lcd_titles.append(lcd_title)
            contractor_names.append(contractor_name)
            statuss.append(status)
            start_dates.append(start_date)
            end_dates.append(end_date)
            release_dates.append(release_date)

            # print("+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-")
            # print(lcd_id)
            # print(lcd_title)
            # print(contractor_name)
            # print(status)
            # print(start_date)
            # print(end_date)
            # print(release_date)

        self.total_data['_LCD_ID'] = lcd_ids
        self.total_data['_LCD_TITLE'] = lcd_titles
        self.total_data['_CONTRACTOR_NAME'] = contractor_names
        self.total_data['_STATUS'] = statuss
        self.total_data['_START_DATE'] = start_dates
        self.total_data['_END_DATE'] = end_dates
        self.total_data['_RELEASE_DATE'] = release_dates

''' Noridian '''
class CMS_scraper2():
    def __init__(self):
        self.url = "https://www.cms.gov/medicare-coverage-database/reports/draft-lcd-status-report.aspx?name=364*1&bc=AQAAAgAAAAAA&#ResultAnchor"
        self.total_data = {}

    def __str__(self):
        return 'CMS2'

    def doProcess(self):
        self.startScraping()
        # db = db_writer('CMS', self.total_data)
        # db.create_table()
        # db.store_data()

        print(str(self) + " completed.")

    def startScraping(self):
        lcd_ids = []
        lcd_titles = []
        contractor_names = []
        statuss = []
        start_dates = []
        end_dates = []
        release_dates = []
        links = []

        html = download(self.url)
        soup = BeautifulSoup(html, 'html.parser')

        rows = soup.select_one(
            "table#ctl00_ctl00_ctl00_CMSGMainContentPlaceHolder_ToolContentPlaceHolder_MCDContentPlaceHolder_DraftLCDReport1_LCDGridView").find_all(
            "tr")

        for i, row in enumerate(rows):
            if i in [0, 1, 2, len(rows) - 2, len(rows) - 1]:
                continue

            lcd_id = row.find("th").text.strip()
            cols = row.find_all("td")
            lcd_title = cols[0].text.strip()
            contractor_name = cols[1].text.strip()
            status = cols[2].text.replace('&nbsp', '').strip()
            try:
                start_date = cols[3].text.replace('&nbsp', '').strip()
                start_date = convertDate(start_date)
            except:
                start_date = ''

            try:
                end_date = cols[4].text.replace('&nbsp', '').strip()
                end_date = convertDate(end_date)
            except:
                end_date = ''

            try:
                release_date = cols[5].text.replace('&nbsp', '').strip()
                release_date = convertDate(release_date)
            except:
                release_date = ''

            lcd_ids.append(lcd_id)
            lcd_titles.append(lcd_title)
            contractor_names.append(contractor_name)
            statuss.append(status)
            start_dates.append(start_date)
            end_dates.append(end_date)
            release_dates.append(release_date)

            # print("+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-")
            # print(lcd_id)
            # print(lcd_title)
            # print(contractor_name)
            # print(status)
            # print(start_date)
            # print(end_date)
            # print(release_date)

        self.total_data['_LCD_ID'] = lcd_ids
        self.total_data['_LCD_TITLE'] = lcd_titles
        self.total_data['_CONTRACTOR_NAME'] = contractor_names
        self.total_data['_STATUS'] = statuss
        self.total_data['_START_DATE'] = start_dates
        self.total_data['_END_DATE'] = end_dates
        self.total_data['_RELEASE_DATE'] = release_dates

''' First Coast '''
class CMS_scraper3():
    def __init__(self):
        self.url = "https://www.cms.gov/medicare-coverage-database/reports/draft-lcd-status-report.aspx?name=368*1&bc=AQAAAgAAAAAA&#ResultAnchor"
        self.total_data = {}

    def __str__(self):
        return 'CMS3'

    def doProcess(self):
        self.startScraping()
        # db = db_writer('CMS', self.total_data)
        # db.create_table()
        # db.store_data()

        print(str(self) + " completed.")

    def startScraping(self):
        lcd_ids = []
        lcd_titles = []
        contractor_names = []
        statuss = []
        start_dates = []
        end_dates = []
        release_dates = []
        links = []

        html = download(self.url)
        soup = BeautifulSoup(html, 'html.parser')

        rows = soup.select_one(
            "table#ctl00_ctl00_ctl00_CMSGMainContentPlaceHolder_ToolContentPlaceHolder_MCDContentPlaceHolder_DraftLCDReport1_LCDGridView").find_all(
            "tr")

        for i, row in enumerate(rows):
            if i in [0, 1, 2, len(rows) - 2, len(rows) - 1]:
                continue

            lcd_id = row.find("th").text.strip()
            cols = row.find_all("td")
            lcd_title = cols[0].text.strip()
            contractor_name = cols[1].text.strip()
            status = cols[2].text.replace('&nbsp', '').strip()
            try:
                start_date = cols[3].text.replace('&nbsp', '').strip()
                start_date = convertDate(start_date)
            except:
                start_date = ''

            try:
                end_date = cols[4].text.replace('&nbsp', '').strip()
                end_date = convertDate(end_date)
            except:
                end_date = ''

            try:
                release_date = cols[5].text.replace('&nbsp', '').strip()
                release_date = convertDate(release_date)
            except:
                release_date = ''

            lcd_ids.append(lcd_id)
            lcd_titles.append(lcd_title)
            contractor_names.append(contractor_name)
            statuss.append(status)
            start_dates.append(start_date)
            end_dates.append(end_date)
            release_dates.append(release_date)

            # print("+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-")
            # print(lcd_id)
            # print(lcd_title)
            # print(contractor_name)
            # print(status)
            # print(start_date)
            # print(end_date)
            # print(release_date)

        self.total_data['_LCD_ID'] = lcd_ids
        self.total_data['_LCD_TITLE'] = lcd_titles
        self.total_data['_CONTRACTOR_NAME'] = contractor_names
        self.total_data['_STATUS'] = statuss
        self.total_data['_START_DATE'] = start_dates
        self.total_data['_END_DATE'] = end_dates
        self.total_data['_RELEASE_DATE'] = release_dates

''' Novitas '''
class CMS_scraper4():
    def __init__(self):
        self.url = "https://www.cms.gov/medicare-coverage-database/reports/draft-lcd-status-report.aspx?name=331*1&bc=AQAAAgAAAAAA&#ResultAnchor"
        self.total_data = {}

    def __str__(self):
        return 'CMS4'

    def doProcess(self):
        self.startScraping()
        # db = db_writer('CMS', self.total_data)
        # db.create_table()
        # db.store_data()

        print(str(self) + " completed.")

    def startScraping(self):
        lcd_ids = []
        lcd_titles = []
        contractor_names = []
        statuss = []
        start_dates = []
        end_dates = []
        release_dates = []
        links = []

        html = download(self.url)
        soup = BeautifulSoup(html, 'html.parser')

        rows = soup.select_one(
            "table#ctl00_ctl00_ctl00_CMSGMainContentPlaceHolder_ToolContentPlaceHolder_MCDContentPlaceHolder_DraftLCDReport1_LCDGridView").find_all(
            "tr")

        for i, row in enumerate(rows):
            if i in [0, 1, 2, len(rows) - 2, len(rows) - 1]:
                continue

            lcd_id = row.find("th").text.strip()
            cols = row.find_all("td")
            lcd_title = cols[0].text.strip()
            contractor_name = cols[1].text.strip()
            status = cols[2].text.replace('&nbsp', '').strip()
            try:
                start_date = cols[3].text.replace('&nbsp', '').strip()
                start_date = convertDate(start_date)
            except:
                start_date = ''

            try:
                end_date = cols[4].text.replace('&nbsp', '').strip()
                end_date = convertDate(end_date)
            except:
                end_date = ''

            try:
                release_date = cols[5].text.replace('&nbsp', '').strip()
                release_date = convertDate(release_date)
            except:
                release_date = ''

            lcd_ids.append(lcd_id)
            lcd_titles.append(lcd_title)
            contractor_names.append(contractor_name)
            statuss.append(status)
            start_dates.append(start_date)
            end_dates.append(end_date)
            release_dates.append(release_date)

            # print("+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-")
            # print(lcd_id)
            # print(lcd_title)
            # print(contractor_name)
            # print(status)
            # print(start_date)
            # print(end_date)
            # print(release_date)

        self.total_data['_LCD_ID'] = lcd_ids
        self.total_data['_LCD_TITLE'] = lcd_titles
        self.total_data['_CONTRACTOR_NAME'] = contractor_names
        self.total_data['_STATUS'] = statuss
        self.total_data['_START_DATE'] = start_dates
        self.total_data['_END_DATE'] = end_dates
        self.total_data['_RELEASE_DATE'] = release_dates

''' CGS '''
class CMS_scraper5():
    def __init__(self):
        self.url = "https://www.cms.gov/medicare-coverage-database/reports/draft-lcd-status-report.aspx?name=239*1&bc=AQAAAgAAAAAA&#ResultAnchor"
        self.total_data = {}

    def __str__(self):
        return 'CMS5'

    def doProcess(self):
        self.startScraping()
        # db = db_writer('CMS', self.total_data)
        # db.create_table()
        # db.store_data()

        print(str(self) + " completed.")

    def startScraping(self):
        lcd_ids = []
        lcd_titles = []
        contractor_names = []
        statuss = []
        start_dates = []
        end_dates = []
        release_dates = []
        links = []

        html = download(self.url)
        soup = BeautifulSoup(html, 'html.parser')

        rows = soup.select_one(
            "table#ctl00_ctl00_ctl00_CMSGMainContentPlaceHolder_ToolContentPlaceHolder_MCDContentPlaceHolder_DraftLCDReport1_LCDGridView").find_all(
            "tr")

        for i, row in enumerate(rows):
            if i in [0, 1, 2, len(rows) - 2, len(rows) - 1]:
                continue

            lcd_id = row.find("th").text.strip()
            cols = row.find_all("td")
            lcd_title = cols[0].text.strip()
            contractor_name = cols[1].text.strip()
            status = cols[2].text.replace('&nbsp', '').strip()
            try:
                start_date = cols[3].text.replace('&nbsp', '').strip()
                start_date = convertDate(start_date)
            except:
                start_date = ''

            try:
                end_date = cols[4].text.replace('&nbsp', '').strip()
                end_date = convertDate(end_date)
            except:
                end_date = ''

            try:
                release_date = cols[5].text.replace('&nbsp', '').strip()
                release_date = convertDate(release_date)
            except:
                release_date = ''

            lcd_ids.append(lcd_id)
            lcd_titles.append(lcd_title)
            contractor_names.append(contractor_name)
            statuss.append(status)
            start_dates.append(start_date)
            end_dates.append(end_date)
            release_dates.append(release_date)

            # print("+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-")
            # print(lcd_id)
            # print(lcd_title)
            # print(contractor_name)
            # print(status)
            # print(start_date)
            # print(end_date)
            # print(release_date)

        self.total_data['_LCD_ID'] = lcd_ids
        self.total_data['_LCD_TITLE'] = lcd_titles
        self.total_data['_CONTRACTOR_NAME'] = contractor_names
        self.total_data['_STATUS'] = statuss
        self.total_data['_START_DATE'] = start_dates
        self.total_data['_END_DATE'] = end_dates
        self.total_data['_RELEASE_DATE'] = release_dates

class HHS_scraper():
    def __init__(self):
        base_url = 'https://www.federalregister.gov/documents/search?conditions%5Bagencies%5D%5B%5D=health-and-human' \
                   '-services-department&conditions%5Bpublication_date%5D%5Bgte%5D={0}%2F{1}%2F{2}'
        self.urls = []
        curDate = datetime.now() - timedelta(days=10)
        curDateStr = str(curDate.date()).split('-')
        base_url = base_url.format(curDateStr[1], curDateStr[2], curDateStr[0])

        for i in range(1, 100):
            url = base_url + '&page={0}'.format(i)
            self.urls.append(url)

        self.total_data = {}

    def __str__(self):
        return 'HHS'

    def doProcess(self):
        self.startScraping()
        # db = db_writer('HHS', self.total_data)
        # db.create_table()
        # db.store_data()

        print(str(self) + " completed.")

    def startScraping(self):
        dates = []
        agencies = []
        titles = []
        descs = []

        for i, url in enumerate(self.urls):
            html = download(url)
            soup = BeautifulSoup(html, 'html.parser')
            rows = soup.find_all("div", {"class": "document-wrapper"})
            for row in rows:
                try:
                    title = row.find("h5").text.strip()
                except:
                    title = ''
                try:
                    agency = row.find("p", {"class": "metadata"}).find_all("a")[0].text.strip()
                except:
                    agency = ''
                try:
                    date = row.find("p", {"class": "metadata"}).find_all("a")[1].text.strip()
                    date = convertDate(date)
                except:
                    date = ''
                try:
                    desc = row.find("p", {"class": "description"}).text.strip()
                except:
                    desc = ''

                dates.append(date)
                agencies.append(agency)
                titles.append(title)
                descs.append(desc)

            if 'No documents were found' in soup.text:
                break

        self.total_data['_DATE'] = dates
        self.total_data['_AGENCY'] = agencies
        self.total_data['_TITLE'] = titles
        self.total_data['_DESC'] = descs

class Genome_scraper():
    def __init__(self):
        self.url = "https://www.genomeweb.com/breaking-news"
        self.total_data = {}

    def __str__(self):
        return 'GENOME'

    def doProcess(self):
        self.startScraping()
        # db = db_writer('GENOME', self.total_data)
        # db.create_table()
        # db.store_data()

        print(str(self) + " completed.")

    def startScraping(self):
        dates = []
        links = []
        titles = []
        descs = []

        html = download(self.url)
        soup = BeautifulSoup(html, 'html.parser')

        rows = soup.select_one("div.view-breaking-news").select("div.views-row")

        for row in rows:
            date = row.select_one("span.date-display-single").text.strip()
            date = invertDate1(date)
            date = convertDate(date)
            title = row.select_one("h3").text.strip()
            link = urljoin(self.url, row.select_one("h3 > a").get('href'))
            desc = row.select_one("div.fieldlayout-body").text.strip()

            dates.append(date)
            links.append(link)
            titles.append(title)
            descs.append(desc)

        self.total_data['_DATE'] = dates
        self.total_data['_LINK'] = links
        self.total_data['_TITLE'] = titles
        self.total_data['_DESC'] = descs

class Axios_scraper():
    def __init__(self):
        self.url = 'https://www.axios.com/health-care/'
        self.total_data = {}

    def __str__(self):
        return 'AXIOS'

    def doProcess(self):
        self.startScraping()
        # db = db_writer('AXIOS', self.total_data)
        # db.create_table()
        # db.store_data()

        print(str(self) + " completed.")

    def startScraping(self):
        dates = []
        authors = []
        titles = []
        descs = []

        # driver = webdriver.PhantomJS('WebDriver/phantomjs.exe')
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument('--disable-gpu')  # Last I checked this was necessary.
        driver = webdriver.Chrome(chrome_options=chrome_options, executable_path='WebDriver/chromedriver.exe')
        driver.maximize_window()
        driver.get(self.url)
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        posts = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.story-card"))
        )

        for i, post in enumerate(posts):
            if i == 20:
                break

            author_rows = WebDriverWait(post, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.StoryHeader__author--3R4v5"))
            )

            author_name = ""
            for author_row in author_rows:
                author_name += author_row.text + " "

            date = post.find_element_by_css_selector('span.StoryHeader__date--1ij89').text

            date = invertDate2(date)
            date = convertDate(date)

            title = post.find_element_by_css_selector('div.Headline__headline--2AbDE').text.strip()

            desc_rows = post.find_elements_by_css_selector("p.StoryBody__paragraph--2-Doz")
            desc = ""
            for desc_row in desc_rows:
                desc += desc_row.text

            dates.append(date)
            authors.append(author_name)
            titles.append(title)
            descs.append(desc)

        driver.quit()

        self.total_data['_DATE'] = dates
        self.total_data['_AUTHOR'] = authors
        self.total_data['_TITLE'] = titles
        self.total_data['_DESC'] = descs

class Orange_scraper1():
    def __init__(self):
        self.url = 'https://www.fda.gov/downloads/Drugs/InformationOnDrugs/UCM163762.zip'
        self.txt_name = "products.txt"
        self.total_data = {}

    def __str__(self):
        return 'ORANGE1'

    def doProcess(self):
        self.startScraping()
        # db = db_writer('ORANGE1', self.total_data)
        # db.create_table()
        # db.store_data()

        print(str(self) + " completed.")

    def startScraping(self):
        ingredients = []
        dfs = []
        routes = []
        trades = []
        applicants = []

        ''' Downloading zip file and unzipping it '''
        self.dest = os.getcwd() + "\\Data"
        app = zip_downloader(self.url, self.dest)
        app.startDownloading()

        ''' Reading all data '''
        companies_nms = []
        try:
            input_xls = xlrd.open_workbook('Data/Scraper Company  Names.xls')
            sheet = input_xls.sheet_by_index(0)
            for rx in range(sheet.nrows):
                if sheet.row(rx)[0].value != '' and sheet.row(rx)[0].value != 'Company Name':
                    companies_nms.append(sheet.row(rx)[0].value)

        except:
            pass

        txt_file = open(self.dest + "\\" + self.txt_name, 'r')
        rows = txt_file.read().split('\n')

        rows_ex = []
        for row in rows:
            if row is not '':
                rows_ex.append(row.split('~'))

        data_ex = rows_ex[1:]

        ''' Filtering data '''
        display_data = []
        for company in companies_nms:
            for i, row in enumerate(data_ex):
                search_words = company.split(' ')
                app_fullname = row[-1]

                for i in range(len(search_words)):
                    search_word = ' '.join(search_words[:i + 1])
                    stop_words = ['.', ',', ';', '(', ')', '&', '  ']

                    for stop_word in stop_words:
                        while (stop_word in app_fullname):
                            app_fullname = app_fullname.replace(stop_word, ' ')

                    if search_word in app_fullname.split(' '):
                        row_disp = row[:4]
                        row_disp = [row_disp[0], row_disp[1].split(';')[0], row_disp[1].split(';')[1], row_disp[2],
                                    row_disp[3]]

                        if row_disp not in display_data:
                            display_data.append(row_disp)

                            ingredients.append(row_disp[0])
                            dfs.append(row_disp[1])
                            routes.append(row_disp[2])
                            trades.append(row_disp[3])
                            applicants.append(row_disp[4])

                        break

        self.total_data['_INGREDIENT'] = ingredients
        self.total_data['_DF'] = dfs
        self.total_data['_ROUTE'] = routes
        self.total_data['_TRADE'] = trades
        self.total_data['_APPLICANT'] = applicants

class Orange_scraper2():
    def __init__(self):
        self.base_url = "https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm?event=reportsSearch.process"
        self.total_data = {}

    def __str__(self):
        return 'ORANGE2'

    def doProcess(self):
        self.startScraping()
        # db = db_writer('ORANGE2', self.total_data)
        # db.create_table()
        # db.store_data()

        print(str(self) + " completed.")

    def startScraping(self):
        dates = []
        drugs = []
        submissions = []
        ingredients = []
        companies = []
        classifications = []
        statuss = []

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:57.0) Gecko/20100101 Firefox/57.0",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            "Host": "www.accessdata.fda.gov",
            "Referer": "https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm?event=reportsSearch.process",
            "Upgrade-Insecure-Requests": "1",
        }

        curDate = datetime.now()
        year = curDate.year
        curmonth = curDate.month
        premonth = curmonth - 1

        months = [curmonth, premonth]

        for month in months:
            self.url = self.base_url + "&rptName=0&reportSelectMonth={}&reportSelectYear={}".format(month, year)
            r = requests.post(url=self.url, headers=headers)
            soup = BeautifulSoup(r.text, 'html.parser')

            rows = soup.select("table#example_1 > tbody > tr")

            for i, row in enumerate(rows):
                cols = row.select("td")
                date = cols[0].text.strip()
                date = convertDate(date)
                dates.append(date)
                drugs.append(cols[1].text.strip())
                submissions.append(cols[2].text.strip())
                ingredients.append(cols[3].text.strip())
                companies.append(cols[4].text.strip())
                classifications.append(cols[5].text.strip())
                statuss.append(cols[6].text.strip())

        self.total_data['_DATE'] = dates
        self.total_data['_DRUG'] = drugs
        self.total_data['_SUBMISSION'] = submissions
        self.total_data['_INGREDIENT'] = ingredients
        self.total_data['_COMPANY'] = companies
        self.total_data['_CLASSIFICATION'] = classifications
        self.total_data['_STATUS'] = statuss

class Orange_scraper3():
    def __init__(self):
        self.url = "https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm?event=report.page"
        self.total_data = {}

    def __str__(self):
        return 'ORANGE3'

    def doProcess(self):
        self.startScraping()
        # db = db_writer('ORANGE3', self.total_data)
        # db.create_table()
        # db.store_data()

        print(str(self) + " completed.")

    def startScraping(self):
        dates = []
        drugs = []
        ingredients = []
        dosages = []
        submissions = []
        companies = []
        classifications = []
        statuss = []

        html = download(self.url)
        soup = BeautifulSoup(html, 'html.parser')

        date_rows = soup.select("div#example2-tab2 > h4")
        tables = soup.select_one("div#example2-tab2").select("table > tbody")

        for date, table in zip(date_rows, tables):
            date = date.text.strip()
            date = invertDate1(date)
            date = convertDate(date)
            rows = table.select("tr")

            for row in rows:
                cols = row.select("td")
                dates.append(date)
                drugs.append(cols[0].text)
                ingredients.append(cols[1].text)
                dosages.append(cols[2].text)
                submissions.append(cols[3].text)
                companies.append(cols[4].text)
                classifications.append(cols[5].text)
                statuss.append(cols[6].text)

        self.total_data['_DATE'] = dates
        self.total_data['_DRUG'] = drugs
        self.total_data['_INGREDIENT'] = ingredients
        self.total_data['_DOSAGE'] = dosages
        self.total_data['_SUBMISSION'] = submissions
        self.total_data['_COMPANY'] = companies
        self.total_data['_CLASSIFICATION'] = classifications
        self.total_data['_STATUS'] = statuss

class Clia_scraper():
    def __init__(self):
        self.url = "http://www.accessdata.fda.gov/premarket/ftparea/clia_detail.zip"
        self.txt_name = "clia_detail.txt"
        self.total_data = {}

    def __str__(self):
        return 'CLIA'

    def doProcess(self):

        self.startScraping()
        # db = db_writer('CLIA', self.total_data)
        # db.create_table()
        # db.store_data()

        print(str(self) + " completed.")

    def startScraping(self):

        dates = []
        doc_nums = []
        par_nums = []
        analyte_ids = []
        testsys_ids = []
        spec_ids = []
        spec_names = []
        analyte_names = []
        testsys_names = []
        qualifier1s = []
        qualifier2s = []
        complexities = []

        ''' Downloading zip file and unzipping it. '''

        self.dest = os.getcwd() + "\\Data"
        app = zip_downloader(self.url, self.dest)
        app.startDownloading()

        ''' Reading all data '''
        txt_file = open(self.dest + "\\" + self.txt_name, 'r')
        rows = txt_file.read().split('\n')

        ''' Filtering data '''
        rows_ex = []
        for row in rows:
            if row is not '':
                rows_ex.append(row.split('|'))

        data_ex = rows_ex[1:]

        for row in data_ex:
            regex = r"([\d]+)/([\d]+)/([\d]+)[ ]+([\d]+):([\d]+):([\d]+).([\d]+)"
            match = re.findall(regex, row[-1])
            match = list(match[0])
            year = int(match[0])
            month = int(match[1])
            day = int(match[2])
            previous_month = datetime.now() - relativedelta(months=1)

            if datetime(year, month, day) >= previous_month:
                date = row[-1].split(' ')[0]
                date = changeDate(date)
                date = convertDate(date)
                dates.append(date)
                doc_nums.append(row[0])
                par_nums.append(row[1])
                analyte_ids.append(row[2])
                testsys_ids.append(row[3])
                spec_ids.append(row[4])
                spec_names.append(row[5])
                analyte_names.append(row[6])
                testsys_names.append(row[7])
                qualifier1s.append(row[8])
                qualifier2s.append(row[9])
                complexities.append(row[10])

        self.total_data['_DATE'] = dates
        self.total_data['_DOC_NUM'] = doc_nums
        self.total_data['_PAR_NUM'] = par_nums
        self.total_data['_ANALYTE_ID'] = analyte_ids
        self.total_data['_TESTSYS_ID'] = testsys_ids
        self.total_data['_SPEC_ID'] = spec_ids
        self.total_data['_SPEC_NAME'] = spec_names
        self.total_data['_ANALYTE_NAME'] = analyte_names
        self.total_data['_TESTSYS_NAME'] = testsys_names
        self.total_data['_QUALIFIER1'] = qualifier1s
        self.total_data['_QUALIFIER2'] = qualifier2s
        self.total_data['_COMPLEXITY'] = complexities

class Fed_scraper1():
    def __init__(self):
        base_url = 'https://www.federalregister.gov/documents/search?conditions%5Bagencies%5D%5B%5D=health-and-human-services-department&conditions%5Bpublication_date%5D%5Bgte%5D={0}%2F{1}%2F{2}&conditions%5Btopics%5D=medical-devices'
        self.urls = []
        curDate = datetime.now() - timedelta(days=60)
        curDateStr = str(curDate.date()).split('-')
        base_url = base_url.format(curDateStr[1], curDateStr[2], curDateStr[0])
        # base_url = base_url.format('01', '01', '2017')

        for i in range(1, 100):
            url = base_url + '&page={0}'.format(i)
            self.urls.append(url)

        self.total_data = {}

    def __str__(self):
        return 'Fed1'

    def doProcess(self):
        self.startScraping()
        # db = db_writer('FED1', self.total_data)
        # db.create_table()
        # db.store_data()

        print(str(self) + " completed.")

    def startScraping(self):
        dates = []
        agencies = []
        titles = []
        descs = []

        for i, url in enumerate(self.urls):
            html = download(url)
            soup = BeautifulSoup(html, 'html.parser')
            rows = soup.find_all("div", {"class": "document-wrapper"})
            for row in rows:
                try:
                    title = row.find("h5").text.strip()
                except:
                    title = ''
                try:
                    agency = row.find("p", {"class": "metadata"}).find_all("a")[0].text.strip()
                except:
                    agency = ''
                try:
                    date = row.find("p", {"class": "metadata"}).find_all("a")[1].text.strip()
                    date = convertDate(date)
                except:
                    date = ''
                try:
                    desc = row.find("p", {"class": "description"}).text.strip()
                except:
                    desc = ''

                dates.append(date)
                agencies.append(agency)
                titles.append(title)
                descs.append(desc)

            if 'No documents were found' in soup.text:
                break

        self.total_data['_DATE'] = dates
        self.total_data['_AGENCY'] = agencies
        self.total_data['_TITLE'] = titles
        self.total_data['_DESC'] = descs

class Fed_scraper2():
    def __init__(self):
        base_url = 'https://www.federalregister.gov/documents/search?conditions%5Bagencies%5D%5B%5D=health-and-human-services-department&conditions%5Bpublication_date%5D%5Bgte%5D={0}%2F{1}%2F{2}&conditions%5Btopics%5D=medicare'
        self.urls = []
        curDate = datetime.now() - timedelta(days=60)
        curDateStr = str(curDate.date()).split('-')
        base_url = base_url.format(curDateStr[1], curDateStr[2], curDateStr[0])
        # base_url = base_url.format('01', '01', '2017')

        for i in range(1, 100):
            url = base_url + '&page={0}'.format(i)
            self.urls.append(url)

        self.total_data = {}

    def __str__(self):
        return 'Fed2'

    def doProcess(self):
        self.startScraping()
        # db = db_writer('FED1', self.total_data)
        # db.create_table()
        # db.store_data()

        print(str(self) + " completed.")

    def startScraping(self):
        dates = []
        agencies = []
        titles = []
        descs = []

        for i, url in enumerate(self.urls):
            html = download(url)
            soup = BeautifulSoup(html, 'html.parser')
            rows = soup.find_all("div", {"class": "document-wrapper"})
            for row in rows:
                try:
                    title = row.find("h5").text.strip()
                except:
                    title = ''
                try:
                    agency = row.find("p", {"class": "metadata"}).find_all("a")[0].text.strip()
                except:
                    agency = ''
                try:
                    date = row.find("p", {"class": "metadata"}).find_all("a")[1].text.strip()
                    date = convertDate(date)
                except:
                    date = ''
                try:
                    desc = row.find("p", {"class": "description"}).text.strip()
                except:
                    desc = ''

                dates.append(date)
                agencies.append(agency)
                titles.append(title)
                descs.append(desc)

            if 'No documents were found' in soup.text:
                break

        self.total_data['_DATE'] = dates
        self.total_data['_AGENCY'] = agencies
        self.total_data['_TITLE'] = titles
        self.total_data['_DESC'] = descs

class Fed_scraper3():
    def __init__(self):
        base_url = 'https://www.federalregister.gov/documents/search?conditions%5Bagencies%5D%5B%5D=health-and-human-services-department&conditions%5Bpublication_date%5D%5Bgte%5D={0}%2F{1}%2F{2}&conditions%5Btopics%5D=biologics'
        self.urls = []
        curDate = datetime.now() - timedelta(days=60)
        curDateStr = str(curDate.date()).split('-')
        base_url = base_url.format(curDateStr[1], curDateStr[2], curDateStr[0])
        # base_url = base_url.format('01', '01', '2017')

        for i in range(1, 100):
            url = base_url + '&page={0}'.format(i)
            self.urls.append(url)

        self.total_data = {}

    def __str__(self):
        return 'Fed3'

    def doProcess(self):
        self.startScraping()
        # db = db_writer('FED1', self.total_data)
        # db.create_table()
        # db.store_data()

        print(str(self) + " completed.")

    def startScraping(self):
        dates = []
        agencies = []
        titles = []
        descs = []

        for i, url in enumerate(self.urls):
            html = download(url)
            soup = BeautifulSoup(html, 'html.parser')
            rows = soup.find_all("div", {"class": "document-wrapper"})
            for row in rows:
                try:
                    title = row.find("h5").text.strip()
                except:
                    title = ''
                try:
                    agency = row.find("p", {"class": "metadata"}).find_all("a")[0].text.strip()
                except:
                    agency = ''
                try:
                    date = row.find("p", {"class": "metadata"}).find_all("a")[1].text.strip()
                    date = convertDate(date)
                except:
                    date = ''
                try:
                    desc = row.find("p", {"class": "description"}).text.strip()
                except:
                    desc = ''

                dates.append(date)
                agencies.append(agency)
                titles.append(title)
                descs.append(desc)

            if 'No documents were found' in soup.text:
                break

        self.total_data['_DATE'] = dates
        self.total_data['_AGENCY'] = agencies
        self.total_data['_TITLE'] = titles
        self.total_data['_DESC'] = descs

class Fed_scraper4():
    def __init__(self):
        base_url = 'https://www.federalregister.gov/documents/search?conditions%5Bagencies%5D%5B%5D=health-and-human-services-department&conditions%5Bpublication_date%5D%5Bgte%5D={0}%2F{1}%2F{2}&conditions%5Btopics%5D=administrative-practice-procedure'
        self.urls = []
        curDate = datetime.now() - timedelta(days=60)
        curDateStr = str(curDate.date()).split('-')
        base_url = base_url.format(curDateStr[1], curDateStr[2], curDateStr[0])
        # base_url = base_url.format('01', '01', '2017')

        for i in range(1, 100):
            url = base_url + '&page={0}'.format(i)
            self.urls.append(url)

        self.total_data = {}

    def __str__(self):
        return 'Fed4'

    def doProcess(self):
        self.startScraping()
        # db = db_writer('FED1', self.total_data)
        # db.create_table()
        # db.store_data()

        print(str(self) + " completed.")

    def startScraping(self):
        dates = []
        agencies = []
        titles = []
        descs = []

        for i, url in enumerate(self.urls):
            html = download(url)
            soup = BeautifulSoup(html, 'html.parser')
            rows = soup.find_all("div", {"class": "document-wrapper"})
            for row in rows:
                try:
                    title = row.find("h5").text.strip()
                except:
                    title = ''
                try:
                    agency = row.find("p", {"class": "metadata"}).find_all("a")[0].text.strip()
                except:
                    agency = ''
                try:
                    date = row.find("p", {"class": "metadata"}).find_all("a")[1].text.strip()
                    date = convertDate(date)
                except:
                    date = ''
                try:
                    desc = row.find("p", {"class": "description"}).text.strip()
                except:
                    desc = ''

                dates.append(date)
                agencies.append(agency)
                titles.append(title)
                descs.append(desc)

            if 'No documents were found' in soup.text:
                break

        self.total_data['_DATE'] = dates
        self.total_data['_AGENCY'] = agencies
        self.total_data['_TITLE'] = titles
        self.total_data['_DESC'] = descs

from PyQt5.QtCore import QThread, pyqtSignal

class total_scraper(QThread):
    countChanged = pyqtSignal(int)

    def __init__(self):
        QThread.__init__(self)
        self.scrapers = [
            FDA_scraper(),
            Press_scraper(),
            Drug_scraper(),
            Maude_scraper(),
            CMS_scraper1(),
            CMS_scraper2(),
            CMS_scraper3(),
            CMS_scraper4(),
            CMS_scraper5(),
            HHS_scraper(),
            # Genome_scraper(),
            # Axios_scraper(),
            # Orange_scraper1(),
            Orange_scraper2(),
            Orange_scraper3(),
            Clia_scraper(),
            Fed_scraper1(),
            Fed_scraper2(),
            Fed_scraper3(),
            Fed_scraper4(),
        ]

        self.cnt = 0
        self.scrapers_cnt = len(self.scrapers)

    def doProcess(self):
        self.threads = []

        for i in range(self.scrapers_cnt):
            thread = threading.Thread(target=self.scrapers[i].doProcess)
            time.sleep(0.5)
            thread.setDaemon(True)
            thread.start()
            self.threads.append(thread)

    def run(self):
        self.doProcess()

        while self.cnt < self.scrapers_cnt:
            for thread in self.threads:
                if not thread.is_alive():
                    self.threads.remove(thread)
                    self.cnt += 1
            time.sleep(0.1)
            self.countChanged.emit(int(self.cnt / self.scrapers_cnt * 100))


if __name__ == '__main__':
    start_t = time.time()
    # app = total_scraper()
    # app = Axios_scraper()
    app = CMS_scraper5()
    app.doProcess()

    elapsed_t = time.time() - start_t
    print(elapsed_t)
