import os
import requests
from bs4 import BeautifulSoup
import csv
import time
import re
from datetime import datetime
import itertools

# The base URL of the website
base_url = "https://identiverse.com"

# The URL of the agenda page
agenda_url = base_url + "/idv23/agenda/"

# Create a new requests session
s = requests.Session()

# Set up headers (replace these with your own headers)
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 Safari/537.36",
}

# CSV header
header = ['id', 'url', 'slug', 'product_name', 'full_description', 'session_location_name',
          'start_time', 'end_time', 'duration_hr:min:sec', 'date', 'product_type', 'topic', 'speaker_count']

# Open the CSV file for writing
with open('Identiverse2023_Agenda.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(header)  # write the header

    # Fetch the content of the page
    response = s.get(agenda_url, headers=headers)

    # If the get request is successful, the status code will be 200
    if response.status_code == 200:
        # Use BeautifulSoup to parse the page content
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all 'a' elements with a class of 'sessionlink'
        links = soup.find_all('a', class_='sessionlink')

        # Navigate to each link and fetch the content of the page
        for i, link in enumerate(links):

            # Get the URL the link points to
            relative_url = link.get('href')

            # Prepend the base URL to form the complete URL
            url = base_url + relative_url
            main_url = url

            # Print the URL (for debugging purposes)
            print(f"Fetching content from {url}")

            # Get the session id from the url
            session_id = url.split('/')[-2]

            # Fetch the content of the page
            response = s.get(url, headers=headers)

            if response.status_code == 200:
                # Use BeautifulSoup to parse the page content
                page_soup = BeautifulSoup(response.content, 'html.parser')

                # Find the product name and slug
                product_name = page_soup.find(
                    class_='session gilroy').get_text().strip()
                slug = re.sub(r'[^a-z0-9]+', '-', product_name.lower())

                # Attempt to find the full description within the 'p' element of the 'blurb' div
                full_description_element = page_soup.find(
                    'div', class_='blurb').find('p')

                # If 'p' element is not found, get text directly from the 'blurb' div
                if full_description_element:
                    full_description = full_description_element.get_text().strip()
                else:
                    full_description = page_soup.find(
                        'div', class_='blurb').get_text().strip()

                # Remove extra spaces from the full description
                full_description = ' '.join(full_description.split())

                # Find the session location name
                session_location_name = page_soup.find(
                    'div', class_='entrydetail').find('strong').get_text().strip()

                # Extract start and end times
                entrydetails = page_soup.find_all('div', class_='entrydetail')
                if len(entrydetails) > 1:
                    entrydetail = entrydetails[1]
                    time_string = entrydetail.get_text(strip=True)
                    times = list(map(str.strip, time_string.split('-')))
                    if len(times) == 1:
                        start_time = times[0]
                        end_time = ''
                    elif len(times) >= 2:
                        start_time, end_time = times[:2]
                    else:
                        start_time, end_time = '', ''
                else:
                    start_time, end_time = '', ''

                def add_minutes_if_needed(time_str):
                    parts = time_str.split()
                    if len(parts) == 2 and ":" not in parts[0]:
                        parts[0] += ":00"
                    return " ".join(parts)

                start_time = add_minutes_if_needed(start_time.strip())
                end_time = add_minutes_if_needed(end_time.strip())

                rl_start_time = datetime.strptime(
                    start_time.strip(), "%I:%M %p")
                rl_end_time = datetime.strptime(end_time.strip(), "%I:%M %p")
                duration = rl_end_time - rl_start_time

                # Find the session date
                session_date_div = page_soup.find(
                    'div', class_='entrydate session')
                if session_date_div is not None:
                    session_date_span = session_date_div.find('span')
                    if session_date_span is not None:
                        date = session_date_span.get_text().strip()
                    else:
                        date = ''
                else:
                    date = ''

                product_type_div = page_soup.find(
                    'div', class_='kicker textuc')
                if product_type_div is not None:
                    product_type = product_type_div.get_text().strip()
                    product_type = product_type.replace(
                        'Identiverse 2023 • ', '')
                else:
                    product_type = ''

                topic_div = page_soup.find(
                    'div', class_='sessiondetail textuc')

                if topic_div is not None:
                    topic = topic_div.get_text().strip()
                else:
                    topic = ''

                # Find all 'a' elements within 'div' elements with a class of 'speaker'
                speaker_links = page_soup.find_all('div', class_='speaker')

                # Initialize empty lists to store the speaker ids, first names and last names
                speaker_ids, speaker_first_names, speaker_last_names, speaker_titles, speaker_companies, speaker_images, social_urls_linkedin, social_urls_twitter, speaker_biographies, speaker_session_ids, speaker_session_dates, speaker_session_times, speaker_session_products = [], [], [], [], [], [], [], [], [], [], [], [], []

                # Navigate to each link and fetch the content of the page
                for speaker_link in speaker_links:
                    url = base_url + speaker_link.a['href']

                    # Get the speaker id from the url
                    speaker_id = url.split('/')[-2]
                    speaker_ids.append(speaker_id)

                    # Fetch the content of the page
                    response_speaker = s.get(url, headers=headers)

                    if response_speaker.status_code == 200:
                        # Use BeautifulSoup to parse the page content
                        speaker_page_soup = BeautifulSoup(
                            response_speaker.content, 'html.parser')

                        # Get the speaker name from their own page
                        speaker_name_div = speaker_page_soup.find(
                            'div', class_='speaker gilroy')
                        if speaker_name_div is not None:
                            speaker_name = speaker_name_div.get_text(
                                strip=True)
                            speaker_first_name, speaker_last_name = speaker_name.split(
                                ' ', 1) if ' ' in speaker_name else (speaker_name, '')
                            speaker_first_names.append(speaker_first_name)
                            speaker_last_names.append(speaker_last_name)
                        else:
                            continue  # Skip this speaker_link if no 'div' with class 'speaker gilroy' is found within it

                        speaker_title_div = speaker_page_soup.find(
                            'div', class_='speakerdetail jobtitle')
                        if speaker_title_div is not None:
                            speaker_title = speaker_title_div.get_text(
                                strip=True)
                            speaker_titles.append(speaker_title)
                        else:
                            continue

                        speaker_company_div = speaker_page_soup.find(
                            'div', class_='speakerdetail company')
                        if speaker_company_div is not None:
                            speaker_company = speaker_company_div.get_text(
                                strip=True)
                            speaker_companies.append(speaker_company)
                        else:
                            continue

                        # Find the speaker detail page div with class='mugshot bgcover'
                        speaker_image_div = speaker_page_soup.find(
                            'div', class_='mugshot bgcover')

                        # Check if the div was found
                        if speaker_image_div is not None:
                            # Get the style attribute of the div
                            style = speaker_image_div.get('style')

                            # Check if the style attribute was found
                            if style is not None:
                                # Use regex to find the URL within the style string
                                match = re.search(r'url\((.*?)\)', style)

                                # Check if a match was found
                                if match is not None:
                                    # Get the first group (the URL) from the match
                                    speaker_image = match.group(1)

                                    # Append the speaker image URL to the speaker_images list
                                    speaker_images.append(speaker_image)
                        else:
                            continue

                        # Find the div with class='social'
                        social_div = speaker_page_soup.find(
                            'div', class_='social')

                        # If the div was found
                        if social_div is not None:
                            # Find all 'a' elements within the div
                            social_links = social_div.find_all('a')

                            # Iterate over each 'a' element
                            for social_link in social_links:
                                # If the 'a' element has class 'linkedin'
                                if 'linkedin' in social_link.get('class', []):
                                    # Append the href attribute to the LinkedIn URLs list
                                    social_urls_linkedin.append(
                                        social_link.get('href'))
                                # Else if the 'a' element has class 'twitter'
                                elif 'twitter' in social_link.get('class', []):
                                    # Append the href attribute to the Twitter URLs list
                                    social_urls_twitter.append(
                                        social_link.get('href'))

                        # If no LinkedIn link was found, append an empty string
                        if len(social_urls_linkedin) == 0:
                            social_urls_linkedin.append('')

                        # If no Twitter link was found, append an empty string
                        if len(social_urls_twitter) == 0:
                            social_urls_twitter.append('')

                        speaker_biography_div = speaker_page_soup.find(
                            'div', class_='blurb')
                        if speaker_biography_div is not None:
                            speaker_biography = speaker_biography_div.get_text(
                                strip=True)
                            speaker_biographies.append(speaker_biography)
                        else:
                            continue

                        session_ids_speaker = []  # To store session ids for current speaker

                        # After fetching the speaker's page
                        session_id_divs = speaker_page_soup.find_all(
                            'div', class_='entrytitle')
                        for session_id_div in session_id_divs:
                            session_id_url = session_id_div.find('a', href=True)[
                                'href']
                            session_id = session_id_url.split(
                                '/')[-2]  # Extract the id from the url
                            session_ids_speaker.append(
                                session_id)  # Store the id

                        # Convert the list of session ids to a string with commas in between
                        session_ids_speaker_str = ' & '.join(
                            session_ids_speaker)

                        if session_ids_speaker_str is not None:
                            speaker_session_ids.append(session_ids_speaker_str)
                        else:
                            continue

                        session_dates_speaker = []  # To store session ids for current speaker

                        # After fetching the speaker's page
                        session_date_divs = speaker_page_soup.find_all(
                            'div', class_='entrydate')
                        for session_date_div in session_date_divs:
                            date_text = session_date_div.span.text
                            session_dates_speaker.append(
                                date_text)  # Store the id

                        # Convert the list of session ids to a string with commas in between
                        session_dates_speaker_str = ' & '.join(
                            session_dates_speaker)

                        if session_dates_speaker_str is not None:
                            speaker_session_dates.append(
                                session_dates_speaker_str)
                        else:
                            continue

                        session_times_speaker = []  # To store session ids for current speaker

                        # After fetching the speaker's page
                        session_time_divs = speaker_page_soup.find_all(
                            'div', class_='entrydetail')
                        for session_time_div in session_time_divs[1::2]:
                            time_text = session_time_div.get_text(
                                strip=True)
                            session_times_speaker.append(
                                time_text)  # Store the id

                        # Convert the list of session ids to a string with commas in between
                        session_times_speaker_str = ' & '.join(
                            session_times_speaker)

                        if session_times_speaker_str is not None:
                            speaker_session_times.append(
                                session_times_speaker_str)
                        else:
                            continue

                        session_products_speaker = []  # To store session ids for current speaker

                        # After fetching the speaker's page
                        session_product_divs = speaker_page_soup.find_all(
                            'div', class_='entrydetail')
                        for session_product_div in session_time_divs[::2]:
                            product_text = session_product_div.get_text(
                                strip=True)
                            session_products_speaker.append(
                                product_text)  # Store the id

                        # Convert the list of session ids to a string with commas in between
                        session_products_speaker_str = ' & '.join(
                            session_products_speaker)

                        if session_products_speaker_str is not None:
                            speaker_session_products.append(
                                session_products_speaker_str)
                        else:
                            continue

                    else:
                        print(
                            f"Failed to fetch page at {url}, status code: {response_speaker.status_code}")

                # Initialize an empty list to store the speaker URLs
                speaker_urls = []

                spk_count = 0

                # Navigate to each link and fetch the content of the page
                for speaker_link in speaker_links:
                    url = base_url + speaker_link.a['href']

                    # Append the speaker URL to the speaker_urls list
                    speaker_urls.append(url)

                    spk_count += 1

                # For each speaker_id, append a corresponding 'id_', 'first_name_' and 'last_name_' column to the CSV header
                for i in range(1, len(speaker_ids) + 1):
                    if f'id_{i}' not in header:
                        header.extend(
                            [f'id_{i}', f'first_name_{i}', f'last_name_{i}', f'url_{i}', f'title_{i}', f'company_{i}', f'image_url_{i}', f'social_url_linkedin_{i}', f'social_url_twitter_{i}', f'biography_{i}', f'session_ids_{i}', f'session_dates_{i}', f'session_times_{i}', f'session_product_types_{i}'])

                # Write the session id, slug, product name, full description, session location name, start and end time, date, product type, topic, and speaker ids, first names and last names to the CSV file
                writer.writerow([session_id, main_url, slug, product_name, full_description, session_location_name, start_time, end_time, duration,
                                date, product_type, topic, spk_count] + list(sum(itertools.zip_longest(speaker_ids, speaker_first_names, speaker_last_names, speaker_urls, speaker_titles, speaker_companies, speaker_images, social_urls_linkedin, social_urls_twitter, speaker_biographies, speaker_session_ids, speaker_session_dates, speaker_session_times, speaker_session_products), ())))

            else:
                print(
                    f"Failed to fetch page at {url}, status code: {response.status_code}")

            # Wait a bit between requests to avoid overwhelming the server
            time.sleep(1)

    else:
        print(f"Failed to fetch page, status code: {response.status_code}")

# Rewrite the CSV file with the updated header
with open('Identiverse2023_Agenda.csv', 'r', encoding='utf-8') as read_obj, open('Identiverse2023_Agenda_temp.csv', 'w', newline='', encoding='utf-8') as write_obj:
    csv_reader = csv.reader(read_obj)
    csv_writer = csv.writer(write_obj)

    # Skip the first row (old header) of the csv_reader
    next(csv_reader)

    csv_writer.writerow(header)  # write the updated header

    for row in csv_reader:
        csv_writer.writerow(row)

# Replace the original CSV file with the temporary one
os.remove('Identiverse2023_Agenda.csv')
os.rename('Identiverse2023_Agenda_temp.csv', 'Identiverse2023_Agenda.csv')
