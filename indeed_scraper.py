import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import mysql.connector
from mysql.connector import Error

# Main function to perform job scraping from Indeed
def indeed_scraper():

    # Get user input for job title, location, and date filter
    job_title = input("Enter job title: ").strip()
    job_location = input("Enter job location: ").strip()
    
    print("\nDate posted filter:")
    print("  1 - Last 24 hours")
    print("  3 - Last 3 days")
    print("  7 - Last 7 days")
    print("  13 - Last 14 days")
    print("  0 - Any time")
    date_filter = input("Choose date filter (enter 1, 3, 7,14, or 0): ").strip()


    # Construct search URL based on input
    base_url = f"https://www.indeed.com/jobs?q={job_title.replace(' ', '+')}&l={job_location.replace(' ', '+')}"
    if date_filter in ['1', '3', '7','14']:
        search_url = f"{base_url}&fromage={date_filter}"
    else:
        search_url = base_url


    # Set up Chrome browser using undetected_chromedriver
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = uc.Chrome(options=options)

    print(f"\n Opening Indeed search for '{job_title}' in '{job_location}'...")
    driver.get(search_url)


     # Check and wait for CAPTCHA (manual resolution)
    if "captcha" in driver.current_url.lower() or "verify" in driver.page_source.lower():
        print("🛑 CAPTCHA detected! Please solve it manually in the browser.")
        input("✅ Press Enter after solving the CAPTCHA...")


      # Wait for job listing elements to load
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.job_seen_beacon"))
        )
    except:
        print(" Job listings did not load properly.")
        driver.quit()
        return

    jobs = driver.find_elements(By.CSS_SELECTOR, "div.job_seen_beacon")

    if not jobs:
        print(" No job listings found.")
        driver.quit()
        return


    # Connect to MySQL database
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="kashaf@234",  
            database="job_scraper"  
        )
    except mysql.connector.Error as err:
        print(f" Database connection error: {err}")
        driver.quit()
        return


      # Create cursor and jobs table if not exists
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            job_title TEXT,
            location TEXT,
            company TEXT,
            salary TEXT,
            job_description TEXT,
            job_types TEXT,
            link TEXT
        )
    """)


     # Loop through each job listing and extract details
    print("\n Scraped Job Listings:\n")
    for i, job in enumerate(jobs, start=1):
        try:
            title = job.find_element(By.CSS_SELECTOR, "h2 span").text.strip()
        except:
            title = "N/A"

        try:
            link_element = job.find_element(By.CSS_SELECTOR, "a")
            link = link_element.get_attribute("href")
            if not link.startswith("http"):
                link = "https://www.indeed.com" + link
        except:
            link = "N/A"


        # Company and location
        try:
            raw_location = job.find_element(By.CLASS_NAME, "company_location").text.strip()
            location_lines = raw_location.split("\n")
            if len(location_lines) > 1:
                company = location_lines[0]
                location = location_lines[1]
            else:
                company = "N/A"
                location = raw_location
        except:
            company = "N/A"
            location = "N/A"

         # Salary
        try:
           salary = driver.find_element(By.XPATH,
            '//div[@aria-label="Pay"]//span[contains(@class, "js-match-insights-provider-1vjtffa") and contains(@class, "e1wnkr790")]'
            ).text
        except:
            salary = None
    

        # Job Type
        try:
            job_types = ''
            job_types_element = driver.find_elements(By.XPATH,
            '//div[@aria-label="Job type"]//span[contains(@class, "js-match-insights-provider-1vjtffa") and contains(@class, "e1wnkr790")]'
            )
            for job_type in job_types_element:
                job_types += job_type.text + ", "
        except:
            job_types = None


          # Job description
        try:
            driver.execute_script("arguments[0].scrollIntoView();", job)
            job.click()
            time.sleep(2)
            job_desc_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "jobDescriptionText"))
            )
            job_desc = job_desc_element.text.strip()
        except:
            job_desc = "N/A"


         # Print job details to console
        print(f"Job {i}:")
        print(f"  Title      : {title}")
        print(f"  Company    : {company}")
        print(f"  Location   : {location}")
        print(f"  Link       : {link}")
        print(f"  salary      : {salary}")
        print(f"  Job Type   : {job_types}")
        print(f"  Description: {job_desc[:200]}...")
        print("-" * 60)


        # Insert job data into the database
        cursor.execute("""
            INSERT INTO jobs (job_title, company,salary,  location, job_types, job_description, link)
            VALUES (%s, %s, %s, %s, %s, %s,%s)
        """, (title, company,salary,  location, job_types, job_desc, link))

     # Commit and close database connection
    db.commit()
    cursor.close()
    db.close()

    # Quit the browser
    driver.quit()
    print("\n✅ Done scraping and saving jobs.")


# Entry point of script
if __name__ == "__main__":
    indeed_scraper()

