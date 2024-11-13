import requests
import threading
from colorama import Fore, Style, init
from dotenv import load_dotenv
import os
import argparse
import re
import time

init(autoreset=True)
load_dotenv()

class URLFetcherApp:
    def __init__(self):
        self.api_key_urlscan = os.getenv("URLSCAN_API_KEY")

    def start_fetching(self, domain, output_file=None, file_type=None):
        if domain:
            ascii_art = """
>>==============================================================<<
|   ____ _               _     _____    _       _                |
|  / ___| |__   ___  ___| |_  |  ___|__| |_ ___| |__   ___ _ __  |
| | |  _| '_ \ / _ \/ __| __| | |_ / _ \ __/ __| '_ \ / _ \ '__| |
| | |_| | | | | (_) \__ \ |_  |  _|  __/ || (__| | | |  __/ |    |
|  \____|_| |_|\___/|___/\__| |_|  \___|\__\___|_| |_|\___|_|    |
|  ⭐⭐⭐⭐⭐ Created by Ghost sec && Ghost Yemen ⭐⭐⭐⭐⭐    ||
>>==============================================================<<
            """
            print(Fore.RED + Style.BRIGHT + ascii_art)
            print(Fore.YELLOW + Style.BRIGHT + "🔍 Starting URL Fetching... Please wait! 😎\n")
            
            urls = self.fetch_urls(domain)
            unique_urls = set(urls)
            
            if file_type:
                file_pattern = re.compile(rf".*\.{file_type}$", re.IGNORECASE)
                filtered_urls = [url for url in unique_urls if file_pattern.search(url)]
            else:
                filtered_urls = unique_urls

            valid_urls = self.filter_valid_urls(filtered_urls)
            
            print(Fore.GREEN + Style.BRIGHT + "🎉 URLs successfully fetched! 🎉\n")
            self.print_urls_with_status(valid_urls)
            
            if output_file:
                self.save_to_file(valid_urls, output_file)
                print(Fore.YELLOW + Style.BRIGHT + f"🚀 Results saved to {output_file} 📝")

    def fetch_urls(self, domain):
        urls = []
        threads = []
        fetchers = [
            self.fetch_from_otx,
            self.fetch_from_wayback,
            self.fetch_from_common_crawl,
            self.fetch_from_urlscan,
        ]
        results = [[] for _ in fetchers]

        def run_fetcher(fetcher, index):
            results[index].extend(fetcher(domain))

        for i, fetcher in enumerate(fetchers):
            thread = threading.Thread(target=run_fetcher, args=(fetcher, i))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        for result in results:
            urls.extend(result)
        return urls

    def fetch_from_otx(self, domain):
        try:
            url = f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/url_list"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                return [url_data['url'] for url_data in data['url_list']]
        except Exception:
            pass  # Error diabaikan
        return []

    def fetch_from_wayback(self, domain):
        try:
            url = f"http://web.archive.org/cdx/search/cdx?url={domain}/*&output=json&fl=original&collapse=urlkey"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                return [entry[0] for entry in data[1:]]
        except Exception:
            pass  # Error diabaikan
        return []

    def fetch_from_common_crawl(self, domain):
        try:
            cc_url = f"https://index.commoncrawl.org/CC-MAIN-2023-09-index?url={domain}&output=json"
            response = requests.get(cc_url)
            if response.status_code == 200:
                return [entry['url'] for entry in response.json()]
        except Exception:
            pass  # Error diabaikan
        return []

    def fetch_from_urlscan(self, domain):
        try:
            url = f"https://urlscan.io/api/v1/search/?q=domain:{domain}"
            headers = {'API-Key': self.api_key_urlscan}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return [result['task']['url'] for result in data['results']]
        except Exception:
            pass
        return []

    def filter_valid_urls(self, urls):
        valid_urls = []
        for url in urls:
            retry_attempts = 3
            while retry_attempts > 0:
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        valid_urls.append(url)
                    break
                except requests.RequestException:
                    retry_attempts -= 1
                    if retry_attempts == 0:
                        pass
                    else:
                        time.sleep(2)
        return valid_urls

    def save_to_file(self, urls, output_file):
        try:
            with open(output_file, 'w') as f:
                f.write("\n".join(urls))
        except Exception:
            pass  # Error diabaikan

    def print_urls_with_status(self, urls):
        if not urls:
            print(Fore.RED + "❌ No valid URLs found.")
        else:
            print(Fore.GREEN + Style.BRIGHT + "🎉 Valid URLs with Status 200:")
            for url in urls:
                print(Fore.GREEN + f"✔️ {url} - Status: {Fore.YELLOW}200 OK 😎")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="URL Fetcher App")
    parser.add_argument("-d", "--domain", type=str, required=True, help="Domain to fetch URLs")
    parser.add_argument("-o", "--output", type=str, help="Output file to save URLs")
    parser.add_argument("-f", "--filetype", type=str, help="File extension to filter (e.g., js, pdf, xls)")
    args = parser.parse_args()

    app = URLFetcherApp()
    app.start_fetching(args.domain, args.output, args.filetype)
