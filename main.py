from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException
from datetime import datetime
import user_details
import smtplib
import requests
import time


def get_existing_jobs(url):
    bearer_headers = {
        "Authorization": f'Bearer {user_details.sheety_token}',
    }
    response = requests.get(url=url, headers=bearer_headers)
    response.raise_for_status()
    data = response.json()["tabellenblatt1"]
    job_list = [data[n]["jobTitle"] for n in range(len(data))]

    return job_list


def add_to_sheets(job_title, company_title, location, link):
    bearer_headers = {
        "Authorization": f'Bearer {user_details.sheety_token}',
    }

    url = user_details.sheety_url
    today = datetime.today()

    params = {
        "tabellenblatt1": {
            "added": today.strftime("%d.%m.%Y"),
            "jobTitle": job_title,
            "companyTitle": company_title,
            "location": location,
            "link": link
        },
    }

    post_response = requests.post(url=url, json=params, headers=bearer_headers)
    # print(post_response.text)


def get_jobs_linkedin(joblist):
    chrome_driver_path = user_details.path_webdriver
    driver = webdriver.Chrome(executable_path=chrome_driver_path)

    url = "https://www.linkedin.com/jobs/search/?geoId=90009749&keywords=projekt&location=Saarland&f_TP=1&redirect=false&position=1&pageNum=0"
    driver.get(url)
    time.sleep(2)
    # total_jobs = driver.find_element_by_xpath('//*[@id="main-content"]/div/section[2]/div[1]/h1/span[1]')

    added_jobs = 0
    all_listings = driver.find_elements_by_css_selector(".result-card__full-card-link")
    for listing in all_listings:
        try:
            listing.click()
            time.sleep(2)
            job_title = driver.find_element_by_xpath('//*[@id="main-content"]/section/div[2]/section[1]/div[1]/div[1]/a/h2')
            company_title = driver.find_element_by_xpath('//*[@id="main-content"]/section/div[2]/section[1]/div[1]/div[1]/h3[1]/span[1]')
            location_title = driver.find_element_by_xpath('//*[@id="main-content"]/section/div[2]/section[1]/div[1]/div[1]/h3[1]/span[2]')
            link = driver.find_element_by_css_selector(".result-card__full-card-link")

            if job_title not in joblist:
                add_to_sheets(job_title.text, company_title.text, location_title.text, link.get_attribute("href"))
                added_jobs += 1

        except ElementClickInterceptedException:
            pass

        time.sleep(2)
        driver.quit()

    return added_jobs


def send_mail(added_jobs):
    with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
        connection.starttls()
        connection.login(user=user_details.my_email, password=user_details.mail_password)
        connection.sendmail(
            from_addr=user_details.my_email,
            to_addrs=user_details.to_tim,
            msg=f"Subject:{added_jobs} new jobs added!\n\n"
                f"{added_jobs} are new on LinkedIn:\n{user_details.link_to_sheet}".encode("utf-8")
        )


def main():
    sheet_url = user_details.sheety_url
    job_list = get_existing_jobs(sheet_url)
    added_jobs = get_jobs_linkedin(job_list)
    send_mail(added_jobs)


if __name__ == '__main__':
    main()