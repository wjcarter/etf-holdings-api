#!/usr/bin/env python3
import argparse
import math
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait

class HoldingsDownloader:
    def __init__(self):
        self.firefox_options = Options()
        self.firefox_options.add_argument("--headless")
        self.firefox_options.add_argument("--no-sandbox")
        self.firefox_options.add_argument("--disable-dev-shm-usage")
        self.firefox_options.add_argument("--disable-gpu")
        self.etf_symbols = []
        self.valid_etfs = []
        self.log_entries = []
        self.file_name = ""
        self.num_files = 0
        self.wait_time = 15
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
        parser.add_argument("-t", "--time", default=15, type=int, help="set max time in seconds for page loads (default: 15)")
        args = parser.parse_args()

        self.quiet_mode = args.quiet
        self.log_mode = args.log
        self.sort_mode = args.alpha
        self.wait_time = args.time
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

    def _convert_units_to_float(self, x):
        start = 0
        if isinstance(x, float):
            return x
        if x[0] == '-':
            return 0
        if x[0] == '$':
            start = 1
        if x[-1] == '%':
            return float(x[:-1]) / 100
        if x[-1] == 'K':
            return float(x[start:-1]) * 1e3
        if x[-1] == 'M':
            return float(x[start:-1]) * 1e6
        if x[-1] == 'B':
            return float(x[start:-1]) * 1e9
        return float(x[start:])

    def _get_etf_from_schwab(self, etf_symbol):
        if not self.quiet_mode:
            print(f"Opening {etf_symbol} database")
        driver = webdriver.Firefox(options=self.firefox_options)
        driver.implicitly_wait(self.wait_time)
        wait = WebDriverWait(driver, 30, poll_frequency=1)
        url = f"https://www.schwab.wallst.com/schwab/Prospect/research/etfs/schwabETF/index.asp?type=holdings&symbol={etf_symbol}"
        try:
            driver.get(url)
            driver.find_element(By.XPATH, "//a[@perpage='60']").click()
        except Exception:
            if not self.quiet_mode:
                print(f"{etf_symbol} not retrieved (invalid or driver error)")
            driver.quit()
            return False

        try:
            page_elt = wait.until(ec.visibility_of_element_located((By.CLASS_NAME, "paginationContainer")))
            num_pages = math.ceil(float(page_elt.text.split(" ")[4]) / 60)
        except Exception:
            driver.quit()
            return False

        if not self.quiet_mode:
            print(f"{etf_symbol}: page 1 of {num_pages} ...", end=" ")
        time.sleep(0.5)
        dataframe_list = [pd.read_html(driver.page_source)[1]]
        if not self.quiet_mode:
            print("complete")

        for page in range(2, num_pages + 1):
            if not self.quiet_mode:
                print(f"{etf_symbol}: page {page} of {num_pages} ...", end=" ")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            next_button = driver.find_element(By.XPATH, f"//li[@pagenumber='{page}']")
            driver.execute_script("arguments[0].click();", next_button)
            while True:
                time.sleep(0.25)
                df = pd.read_html(driver.page_source, match="Symbol")[0]
                if not df.equals(dataframe_list[-1]):
                    break
            dataframe_list.append(df)
            if not self.quiet_mode:
                print("complete")

        df = pd.concat(dataframe_list).drop_duplicates()
        df.columns = ['Symbol', 'Description', 'Portfolio Weight', 'Shares Held', 'Market Value']
        if self.raw_mode:
            df['Portfolio Weight'] = df['Portfolio Weight'].apply(self._convert_units_to_float)
            df['Shares Held'] = df['Shares Held'].apply(self._convert_units_to_float)
            df['Market Value'] = df['Market Value'].apply(self._convert_units_to_float)

        df.to_csv(f"{etf_symbol}-holdings.csv", index=False)

        if self.log_mode:
            driver.execute_script("window.scrollTo(0, -document.body.scrollHeight);")
            try:
                header_elt = driver.find_element(By.XPATH, "//div[@modulename='FirstGlance']")
                header_text = header_elt.text.split("\n")
                full_name = header_text[0].split(f" {etf_symbol}:")[0].encode("ascii", "ignore").decode()
                last_price = header_text[2].split(" ")[0]
                self.log_entries.append([etf_symbol, full_name, last_price, df.shape[0]])
            except Exception:
                pass

        driver.quit()
        if not self.quiet_mode:
            print(f"{etf_symbol}: {df.shape[0]} holdings retrieved\n")
        return True

    def run_schwab_download(self):
        for symbol in self.etf_symbols:
            if symbol in self.valid_etfs:
                continue
            if self._get_etf_from_schwab(symbol):
                self.valid_etfs.append(symbol)
                self.num_files += 1

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
