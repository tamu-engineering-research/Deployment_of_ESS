"""
Created on Wed Jun 28 12:56:39 2023

@author: Andreas Makrides
"""
import pandas as pd
import os
import re
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import requests, zipfile, io


# Set the path to the WebDriver executable (e.g., chromedriver for Chrome), add your own chrome driver
driver_path = r"C:\Users\user\Documents\chromedriver_win32 (1)\chromedriver.exe"
# Set the URL of the web page to navigate
url = 'https://www.ercot.com/mp/data-products/data-product-details?id=NP6-788-CD'
# Set the target path to click and download files
target_path = '//*[@id="reportTable"]/tbody'

#get your current path
path = os.getcwd()

# Configure Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode, no browser window

# Create a new ChromeDriver instance
driver1 = webdriver.Chrome(service=Service(driver_path), options=chrome_options)

# Navigate to the URL
driver1.get(url)
time.sleep(5) 
# Find the target path and get the number of subfolders
driver = WebDriverWait(driver1, 10).until(EC.visibility_of_element_located((By.XPATH, target_path)))

# Finding the table by its attribute which is 'aria-labelledby'
subfolders = []

while len(subfolders) == 0:
    table = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, target_path)))
    subfolders = driver.find_elements(By.XPATH, target_path + '/tr')
    num_subfolders = len(subfolders)

# Iterate through the subfolders
for i in range(num_subfolders-1, 1, -2):
    # Construct the XPath for the link inside each subfolder
    link_xpath = target_path + f'/tr[{i}]/td[4]/a'
    link = driver.find_element(By.XPATH, link_xpath)
    file_url = link.get_attribute('href')
    
    r = requests.get(file_url)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(os.path.join(os.getcwd(), 'raw data'))
    
    # time.sleep(2)
    
# Close the WebDriver
driver1.quit()




