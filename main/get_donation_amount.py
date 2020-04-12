import requests
import json
import openpyxl

class DonationGetter:
    def __init__(self, app_id, headers, api_url, fund_url):
        self.app_id = app_id
        self.fund_url = fund_url
        self.headers = headers
        self.api_url = api_url

    def process_workbook(self, workbook):
        for sheet in workbook:
            if sheet.title == "Summary":
                continue
            else:
                for index, row in enumerate(sheet.iter_rows(min_row=2), start=2):
                    row_shortname = self._get_shortname(row)
                    r_code = self._check_page_exists(row_shortname)
                    if r_code == 200:
                        donation_amount = self._get_donation_amount(row_shortname)
                        row[12].value = donation_amount
                    else:
                        print("page doesn't exist")
        return workbook

    def _check_page_exists(self, shortname):
        head_r = requests.head(
            self.api_url.format(self.app_id, shortname), headers=self.headers
        )
        return head_r.status_code

    def _get_donation_amount(self, shortname):
        get_r = requests.get(
            self.api_url.format(self.app_id, shortname), headers=self.headers
        )
        with open("output.json", "w") as out:
            json.dump(get_r.json(), out)

        return get_r.json()["grandTotalRaisedExcludingGiftAid"]

    def _load_workbook(self):
        return openpyxl.load_workbook(self.excel_location)

    def _get_shortname(self, row):
        shortname = row[11].value.replace(self.fund_url, "")
        return shortname