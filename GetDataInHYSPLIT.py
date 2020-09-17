import pandas as pd
import re
import os
import requests
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

def addzero(x):
    if len(str(x)) == 1:
        x = '0' + str(x)
    return str(x)

def get_URL (startdate, enddate, xtype=1, metdata='reanalysis', metdatasm='reanalysis'):
    datelist = []
    urllist = []
    if metdata == 'reanalysis':
        startdate = str(startdate)
        enddate = str(enddate)
        dates = pd.date_range(start= startdate,end = enddate, freq = 'm')
        for item in dates:
            date = str(item.year) + addzero(item.month)
            metfile = 'RP' + date + '.gbl'
            url = 'https://www.ready.noaa.gov/ready2-bin/extract/extract1a.pl?' + 'xtype=' + str(xtype) + '&metdata=' + metdata + '&metdatasm=' + metdatasm + '&metfile=' + metfile
            datelist.append (date)
            urllist.append (url)
    resultlist = [datelist, urllist]
    return resultlist

def post_param (url, latL, lonL, latR, lonR):
    browser = webdriver.Chrome()
    wait = WebDriverWait(browser, 60)
    errornumber = ''
    dlurl = ''
    dlfig = ''
    project = ''
    try:
        browser.get(url)
        latLinput = wait.until (EC.presence_of_element_located((By.CSS_SELECTOR,'[name=latL]')))
        lonLinput = wait.until (EC.presence_of_element_located((By.CSS_SELECTOR,'[name=lonL]')))
        latRinput = wait.until (EC.presence_of_element_located((By.CSS_SELECTOR,'[name=latR]')))
        lonRinput = wait.until (EC.presence_of_element_located((By.CSS_SELECTOR,'[name=lonR]')))
        submitbutton = wait.until (EC.element_to_be_clickable((By.CSS_SELECTOR, '.center [type=submit]')))
        latLinput.send_keys(latL)
        lonLinput.send_keys(lonL)
        latRinput.send_keys(latR)
        lonRinput.send_keys(lonR)
        submitbutton.click()
    
        project = re.findall('https.*?proc=(.*?)&x=0', browser.current_url)[0]
        submitbutton2 = wait.until (EC.element_to_be_clickable((By.CSS_SELECTOR, '.center [type=submit]')))
        submitbutton2.click()
    
        dlfig = wait.until (EC.presence_of_element_located((By.CSS_SELECTOR,'div center a'))).get_attribute('href')
        dlurl = wait.until (EC.presence_of_element_located((By.CSS_SELECTOR,'div center h2 a'))).get_attribute('href')
    except:
        errornumber = 'Timeout!' 
    finally:
        browser.close()
        return [project, dlurl, dlfig, errornumber] 

def downloaddata (date, dataurl, figurl):
    Dlornot = ''
    date = str(date)
    try:
        project = re.findall('htt.*?extract_(.*?).zip', dataurl)[0]
        data = requests.get(dataurl)
        year = date[0:4]
        if not os.path.exists(year):
            os.mkdir(year)
        datapath = year + '/' + date + ' ' + project + '.zip'
        with open(datapath, 'wb') as f:
            f.write(data.content) 

        fig = requests.get(figurl)
        datapath = year + '/' + date + ' ' + project + '.gif'
        with open(datapath, 'wb') as f:
            f.write(fig.content)
        Dlornot = 'Successfully downloaded!'
    except:
        Dlornot = 'Fail to download.'
    finally:    
        return Dlornot

def main(startdate, enddate, latL, lonL, latR, lonR, xtype=1, metdata='reanalysis', metdatasm='reanalysis'):
    project = []
    dlurl = []
    dlfig = []
    errornumber = []
    dlornotlist = []
    
    getURL = get_URL (startdate= startdate, enddate = enddate, xtype=xtype, metdata=metdata, metdatasm= metdatasm)
    datelist = getURL[0]
    URLlist = getURL[1]
    for pageURL in URLlist:
        postlist = post_param (url=pageURL, latL=latL, lonL=lonL, latR=latR, lonR=lonR)
        project.append (postlist[0])
        dlurl.append (postlist[1])
        dlfig.append (postlist[2])
        errornumber.append (postlist[3])
    
    for x in range(0,len(dlurl)):
        dlornot = downloaddata(date = datelist[x], dataurl = dlurl[x], figurl= dlfig[x])
        dlornotlist.append (dlornot)
    
    resultreport = pd.DataFrame({'Date': datelist,
                                 'Project': project,
                                 'Downloaded': dlornotlist,
                                 'Error': errornumber,
                                 'DataDlURL': dlurl,
                                 'FigDlURL':dlfig})
    savepath = str(datelist[0]) + '-' + str(datelist [-1]) + ' ' + 'report.xlsx'
    resultreport.to_excel(savepath, sheet_name='report', index=False)
    
    print ('Suceessfully Download!')


main(startdate = 19570101, enddate = 19570201, latL = '-10', lonL = '10', latR = '90', lonR = '180')
#It needs pandas, requests, selenium and selenium webdriver.
#Download it by typing "pip install XX"(XX = pandas, requests, selenium.) in Anaconda Prompt (anaconda3) (if you use Anaconda) or CMD.
#For selenium webdriver, in this code, Chrome is used. Please download it in: https://sites.google.com/a/chromium.org/chromedriver/downloads

#startdate and enddate MUST have Year, Month and day. Although Day is not necessary for reanalysis data.
#latL means Lower-left Latitude, lonL means Lower-left Longtitude, 
#Similarly, latR means Upper-right Latitude, lonR means Upper-right Longtitude.
#such 4 coordinates can form a rectangle and download the data in this rectangle.
#If you are not familiar with other parameters, please DO NOT modify other parameters.