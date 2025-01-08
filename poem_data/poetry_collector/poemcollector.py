from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import time
import json
import random
import logging
from datetime import datetime



class PoetryFoundationScraper:
    def __init__(self, delay_range=(2, 4)):
        """
        Initialize the scraper with configurable delay between requests

        Args:
            delay_range (tuple): Min and max seconds to wait between requests
        """
        self.delay_range = delay_range
        self.collected_links = set()
        self.collected_titles = []
        self.setup_logging()
        self.setup_driver()

    def setup_logging(self):
        """Configure logging to track progress and errors"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'poetry_scraper_{timestamp}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_driver(self):
        """Configure Selenium WebDriver with respectful scraping settings"""
        options = webdriver.ChromeOptions()
        options.add_argument('user-agent=PoetryMetadataResearchBot/1.0')
        options.add_argument('--start-maximized')
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def random_delay(self):
        """Add random delay between requests to avoid overloading the server"""
        time.sleep(random.uniform(*self.delay_range))

    def scroll_page(self, scroll_pause_time=1.0):
        """Scroll through the entire page"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:
            # Scroll down
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause_time)

            # Calculate new scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                break

            last_height = new_height

            # Random slight scroll up (20% chance)
            if random.random() < 0.2:
                self.driver.execute_script(
                    "window.scrollTo(0, window.pageYOffset - 200);"
                )
                time.sleep(0.5)

    def get_poem_metadata(self, url):
        """
        Collect basic metadata about a poem (title, author, year, topics)
        Does NOT collect the poem text itself
        """
        try:
            self.driver.get(url)
            self.random_delay()

            metadata = {
                'url': url,
                'poem_title': '',
                'author': '',
                'poem_text': ''
            }

            # Get metadata elements
            parent = self.driver.find_element(By.XPATH, '//*[@id="mainContent"]/article/div/div[1]/div')
            try:
                metadata['poem_title'] = parent.find_element(By.CSS_SELECTOR, 'h1.type-gamma').text
            except:
                pass

            try:
                metadata['author'] = parent.find_element(By.CSS_SELECTOR, 'a.link-underline-off.link-red').text
            except:
                pass

            try:
                poem_div = parent.find_element(By.CLASS_NAME, 'poem-body')
                poem_lines = poem_div.find_elements(By.XPATH, '*')
                metadata['poem_text'] = [line.text for line in poem_lines]
            except:
                pass

            return metadata

        except Exception as e:
            self.logger.error(f"Error scraping {url}: {str(e)}")
            return None

    def collect_links_from_page(self):
        """Collect all poem links from current page"""
        try:
            poem_elements = self.wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, 'a.link-underline-on.link-red')
                )
            )

            links = set()
            for element in poem_elements:
                try:
                    link = element.get_attribute('href')
                    if link and '/poems/' in link:
                        links.add(link)
                except StaleElementReferenceException:
                    continue

            return links

        except TimeoutException:
            self.logger.warning("Timeout while collecting links from page")
            return set()

    def collect_titles_from_page(self):
        """Collect all poem links from current page"""
        try:

            parent = self.driver.find_element(By.XPATH, '//*[@id="mainContent"]/div/div/div[2]/div[1]/ul')
            poem_titles = parent.find_elements(By.CLASS_NAME, 'flex-1')

            link_text = []
            for element in poem_titles:
                try:
                    title = element.find_element(By.CSS_SELECTOR, 'a.link-underline-on.link-red').text
                    find_tags = element.find_elements(By.CSS_SELECTOR, 'a.button-small.button-gray.uppercase')
                    tags = [tag.get_attribute("textContent") for tag in find_tags]
                    link = {'title': title, 'tags': tags}
                    link_text.append(link)
                except StaleElementReferenceException:
                    continue

            return link_text

        except TimeoutException:
            self.logger.warning("Timeout while collecting links from page")
            return set()

    def click_next_page(self):
        """Attempt to click the next page button"""
        try:
            # Poetry Foundation typically uses 'next' class for pagination
            next_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[aria-label="Next Page"]'))
            )
            self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            time.sleep(0.5)
            next_button.click()
            return True

        except (TimeoutException, StaleElementReferenceException):
            return False

    def collect_all_poem_links(self, start_url="https://www.poetryfoundation.org/poems/browse/verse-forms", max_pages=None):
        """
        Collect poem links from all pages

        Args:
            start_url (str): URL to start collecting from
            max_pages (int): Maximum number of pages to traverse (None for unlimited)
        """
        current_page = 1

        try:
            self.driver.get(start_url)
            self.logger.info(f"Starting link collection at: {start_url}")

            while True:
                self.logger.info(f"Collecting links from page {current_page}")

                # Scroll through current page
                self.scroll_page()
                self.random_delay()

                # Collect links from current page
                new_links = self.collect_links_from_page()
                new_titles = self.collect_titles_from_page()
                self.collected_links.update(new_links)
                self.collected_titles.extend(new_titles)
                self.logger.info(f"Found {len(new_links)} new poem links on page {current_page}")

                # Check if we've reached the maximum pages
                if max_pages and current_page >= max_pages:
                    self.logger.info(f"Reached maximum pages limit: {max_pages}")
                    break

                # Try to go to next page
                if not self.click_next_page():
                    self.logger.info("No more pages to traverse")
                    break

                current_page += 1
                self.random_delay()

        except Exception as e:
            self.logger.error(f"Error during link collection: {str(e)}")

        finally:
            self.logger.info(f"Total unique poem links collected: {len(self.collected_links)}")

    def scrape_poems_metadata(self, max_poems=None):
        """
        Scrape metadata for collected poem links

        Args:
            max_poems (int): Maximum number of poems to scrape (None for all)
        """
        results = []
        links_to_scrape = list(self.collected_links)[:max_poems] if max_poems else list(self.collected_links)


        self.logger.info(f"Starting to scrape metadata for {len(links_to_scrape)} poems")

        for i, link in enumerate(links_to_scrape, 1):
            self.logger.info(f"Scraping metadata for poem {i}/{len(links_to_scrape)}")
            metadata = self.get_poem_metadata(link)
            if metadata:
                results.append(metadata)
            self.random_delay()

        return results

    def save_results(self, results, filename=None):
        """Save results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'poem_metadata_{timestamp}.json'

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Successfully saved metadata to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving results: {str(e)}")

    def cleanup(self):
        """Close the browser and perform cleanup"""
        self.driver.quit()


def main():
    scraper = PoetryFoundationScraper()
    try:
        # First collect all poem links (adjust max_pages as needed)
        scraper.collect_all_poem_links(max_pages=141)

        # Then scrape metadata for collected links (adjust max_poems as needed)
        results = scraper.scrape_poems_metadata(max_poems=2801)

        # Save the results
        scraper.save_results(results)

        # Write tags to csv
        filename = 'verse_forms_poem_tags.csv'
        with open(filename, 'w') as file:
            # Write the header
            header = ','.join(scraper.collected_titles[0].keys())  # Get the keys from the first dictionary
            file.write(header + '\n')  # Write header followed by a newline

            # Write the data
            for entry in scraper.collected_titles:
                row = ','.join(str(entry[key]) for key in entry)  # Convert each value to string and join with commas
                file.write(row + '\n')  # Write each row followed by a newline

        print(f"Data exported to {filename}")

    finally:
        scraper.cleanup()


if __name__ == "__main__":
    main()
