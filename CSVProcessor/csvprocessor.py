import argparse
import csv
import logging
import logging.config
import os
import re
import json
from typing import Tuple, Optional, List

from celery_app import app

with open("logging.json", 'rt') as f:
    config = json.load(f)
    logging.config.dictConfig(config)


class CSVProcessor:
    """
    Class that allows to read a csv and send the full name and email fields to a broker
    in order to be added to a database
    """

    # class variable that stores compiled  regex to validate email according to https://emailregex.com/
    email_pattern = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")

    def __init__(self, file_path: str):
        """
        Constructor that sets the file path and init the logger
        :param file_path: Path of csv
        """
        self.file_path = file_path
        self.logger = logging.getLogger('csvprocessor')

    def process_row(self, pos: int, row: List) -> Tuple[Optional[str], Optional[str]]:
        """
        Check length of row and extracts full_name and email without trailing spaces
        Then checks that full name is not empty and  the email matches with the email_pattern regex
        :param pos: Position of row in the csv
        :param row: List that represents the csv row
        :return: Tuple of length 2 with valid full_name and email or None in both fields
        """
        if len(row) > 1:
            full_name = row[0].strip()  # simple cleaning of extra whitespaces
            email = row[1].strip()
            if full_name != "":
                if self.email_pattern.match(email):
                    return full_name, email
                else:
                    self.logger.debug(f"Skipping row {pos} because it has invalid email {email}")
            else:
                self.logger.debug(f"Skipping row {pos} because it has empty full name")
        else:
            self.logger.debug(f"Skipping row {pos} because it's missing fields")
        return None, None

    def read_csv(self):
        """
        Generator that opens and reads the csv in self.file_path
         and yields the processed full_name and email from the rows
        """
        try:
            with open(self.file_path, encoding='utf-8') as f:
                reader = csv.reader(f)
                try:
                    for i, row in enumerate(reader):
                        if len(row) > 1:
                            full_name, email = self.process_row(i, row)
                            if full_name is not None:
                                yield full_name, email
                except UnicodeDecodeError:
                    self.logger.exception("Character in file not encoded in utf-8")
                except csv.Error:
                    self.logger.exception("CSV file formatted wrong")

        except OSError:
            self.logger.exception("Error reading CSV file")

    def process_csv(self):
        """
        Process data from csv in self.file_path and sends it to the broker
        """
        self.logger.info("Started processing of csv")
        for full_name, email in self.read_csv():
            self.logger.info(f"Putting ({full_name}, {email}) into the queue")
            app.send_task('tasks.add_to_db', args=(full_name, email))

        self.logger.info("Finished processing of csv")


if __name__ == '__main__':
    def valid_csv_path(p: str) -> str:
        """
        Check if the path given exists
        :param p: Path given
        :return: Path given if valid
        :raises: ArgumentTypeError if path given is not valid
        """
        if os.path.exists(p):
            return p
        else:
            msg = "Not a valid path"
            raise argparse.ArgumentTypeError(msg)


    parser = argparse.ArgumentParser()
    parser.add_argument('-csv', '--csv-path', type=valid_csv_path, required=True)
    args = parser.parse_args()
    file_path = args.csv_path
    csv_proc = CSVProcessor(file_path)
    csv_proc.process_csv()
