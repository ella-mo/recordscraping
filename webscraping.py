import os.path
import requests
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.parse import urlparse

email = ''
last_name = ''
first_name = ''
download_directory = ''
txt_file = ''

with open(txt_file, 'r') as url_file: #txt_file holds website urls
    while True:
        url = url_file.readline()
        if not url:
            break
        driver = webdriver.Chrome()
        driver.implicitly_wait(30)
        driver.get(url)

        #login
        driver.find_element(By.XPATH, "(//div[@class='Content_lineContainer__WZS9m'])[9]").click()
        driver.find_element(By.ID, ':r0:').send_keys(email)
        driver.find_element(By.ID, ':r1:').send_keys(last_name)
        driver.find_element(Bu.ID, ':r2:').send_keys(first_name)

        footer = driver.find_element(By.XPATH, "(//footer[@class='Footer_footer__uKHUT'])")
        footer.find_element(By.XPATH,
                            "(//button[@class='button ripple-container sc-dicizt bdqNkj cfp-button-spinner Footer_approveButton__epXEV'])").click()
        #receipt
        receipt = driver.current_window_handle
        buttons = driver.find_elements(By.XPATH, "(//button[@class='button ripple-container'])")
        count = 0
        for button in buttons:
            try:
                button.click()
                count += 1
                driver.switch_to.window(driver.window_handles[-1])
                current_url = driver.current_url
                filename = os.path.basename(urlparse(current_url.path))
                #api render
                #downloading pdf to folder
                api_url = requests.get(current_url, stream=True)
                filepath = os.path.join(download_directory, filename)

                with open(filepath, 'wb') as folder:
                    folder.write(api_url.content)

                driver.switch_to.window(receipt)
            except selenium.common.exceptions.ElementClickInterceptedExcption:
                print(count)
                continue
        driver.quit()

#Close the Webdriver
driver.close()

