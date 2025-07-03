import argparse
import pandas as pd
import requests
from bs4 import BeautifulSoup

class HoldingsDownloader:
    def __init__(self):
        self.etf_symbols = []
        self.valid_etfs = []
        self.log_entries = []
        self.file_name = ""
        self.num_files = 0
        self.log_mode = False
        self.quiet_mode = False
        self.sort_mode = False
        self.raw_mode = False
        self._parse_command_args()
        if self.file_name:
            self._read_input_file()
        if self.sort_mode:
            self.etf_symbols.sort()

    def _parse_command_args(self):
        parser = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=27))
        title_group = parser.add_argument_group(title="required arguments")
        input_type_group = title_group.add_mutually_exclusive_group(required=True)
        input_type_group.add_argument("--symbol", nargs='+', metavar="SYM", help="specify one or more ETF symbols")
        input_type_group.add_argument("--file", metavar="FILE", help="specify a file containing a list of ETF symbols")
        parser.add_argument("-r", "--raw", action="store_true", help="save raw data without symbols or units")
        parser.add_argument("-l", "--log", action="store_true", help="create a log of the downloaded ETFs in etf-log.csv")
        parser.add_argument("-a", "--alpha", action="store_true", help="sort ETF symbols into alphabetical order for output")
        parser.add_argument("-q", "--quiet", action="store_true", help="suppress verbose terminal output")
        args = parser.parse_args()

        self.quiet_mode = args.quiet
        self.log_mode = args.log
        self.sort_mode = args.alpha
        self.raw_mode = args.raw
        if args.file:
            self.file_name = args.file
        if args.symbol:
            self.etf_symbols = args.symbol

    def _read_input_file(self):
        if not self.quiet_mode:
            print(f"Reading symbols from {self.file_name} ...", end=" ")
        with open(self.file_name, 'r') as input_file:
            for name in input_file:
                self.etf_symbols.append(name.strip())
        if not self.quiet_mode:
            print("complete")

    def _fetch_with_browserless(self, url):
        browserless_url = "https://chrome.browserless.io/content?token=2Sc7eNrdlusLqR65ee2613fadc023cdc94d5c7688bc894634"
        try:
            response = requests.post(
                browserless_url,
                json={"url": url}
            )
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            return None

    def run_schwab_download(self):
        for symbol in self.etf_symbols:
            if symbol in self.valid_etfs:
                continue

            url = f"https://www.schwab.com/etfs/{symbol}"
            html = self._fetch_with_browserless(url)

            if html:
                try:
                    df = pd.read_html(html, match="Symbol")[0]
                    df.to_csv(f"{symbol}-holdings.csv", index=False)
                    print(f"{symbol}: {len(df)} holdings retrieved")
                    self.valid_etfs.append(symbol)
                    self.num_files += 1
                except Exception as e:
                    print(f"{symbol}: Error parsing HTML - {e}")
            else:
                print(f"{symbol}: Failed to fetch HTML")

    def generate_log_file(self):
        if not self.quiet_mode:
            print("Generating log file...", end=' ')
        log_df = pd.DataFrame(self.log_entries, columns=['Symbol', 'Name', 'Last Price', 'Number of Holdings'])
        log_df.to_csv("etf-log.csv", index=False)
        self.num_files += 1
        if not self.quiet_mode:
            print("complete")

    def print_end_summary(self):
        print(f"\n{self.num_files} file(s) have been generated for {len(self.valid_etfs)} ETF(s):")
        if self.log_mode:
            print("etf-log.csv")
        for symbol in self.valid_etfs:
            print(f"{symbol}-holdings.csv")

def main():
    downloader = HoldingsDownloader()
    downloader.run_schwab_download()
    if downloader.log_mode:
        downloader.generate_log_file()
    if not downloader.quiet_mode:
        downloader.print_end_summary()

if __name__ == "__main__":
    main()
