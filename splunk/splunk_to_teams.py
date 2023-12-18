import requests
import datetime
import xml.etree.ElementTree as ET
import json
import os
import sys
from time import sleep

def is_weekday():
    today = datetime.datetime.today().weekday()
    return 0 <= today <= 4

def send_curl_request(url):
    token = os.getenv('SPLUNK_TOKEN')
    headers = {
        'Authorization': f'Bearer {token}',
    }
    response = requests.get(url, headers=headers, verify=False)
    return response

def extract_latest_job_link(xml_response):
    root = ET.fromstring(xml_response)
    entries = root.findall('.//{http://www.w3.org/2005/Atom}entry')
    if not entries:
        print("No entries found in the response.")
        return None
    latest_entry = entries[-1]
    link = latest_entry.find('.//{http://www.w3.org/2005/Atom}link').get('href')
    return link

def parse_results(xml_response):
    root = ET.fromstring(xml_response)
    results = []
    for result in root.findall('.//result'):
        entry = {}
        for field in result.findall('field'):
            key = field.get('k')
            value = field.find('.//text').text if field.find('.//text') is not None else None
            entry[key] = value
        results.append(entry)
    return results

def format_results_as_markdown_table(results):
    if not results:
        return "No results found."

    headers = results[0].keys()
    table = "| " + " | ".join(headers) + " |\n"
    table += "| " + " | ".join(["---"] * len(headers)) + " |\n"

    for result in results:
        row = "| " + " | ".join(result.get(h, "") for h in headers) + " |\n"
        table += row

    return table

def post_to_teams(results):
    webhook_url = os.getenv('TEAMS_WEBHOOK_URL')
    markdown_message = format_results_as_markdown_table(results)
    message = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "text": markdown_message
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(webhook_url, headers=headers, data=json.dumps(message))
    return response.status_code

def main():
    while True:
        if is_weekday():
            try:
                initial_url = "https://<host>/services/saved/searches/<search_name>/history"
                response = send_curl_request(initial_url)
                if response.status_code != 200:
                    print(f"Failed to retrieve job history: {response.status_code}")
                    sys.exit(1)

                latest_job_link = extract_latest_job_link(response.text)
                if not latest_job_link:
                    print("No job link found.")
                    sys.exit(1)

                job_results_url = f"https://<host>{latest_job_link}/results"
                response = send_curl_request(job_results_url)
                if response.status_code != 200:
                    print(f"Failed to retrieve job results: {response.status_code}")
                    sys.exit(1)

                parsed_results = parse_results(response.text)
                if not parsed_results:
                    print("No results found or failed to parse results.")
                    sys.exit(1)

                status_code = post_to_teams(parsed_results)
                if status_code != 200:
                    print(f"Failed to post to Teams: {status_code}")
                    sys.exit(1)

            except Exception as e:
                print(f"Error occurred: {e}")
                sys.exit(1)

        else:
            print("It's not a weekday. No request sent.")

        sleep(86400)

if __name__ == "__main__":
    main()
