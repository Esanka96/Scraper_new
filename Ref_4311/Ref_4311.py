import re
import requests
from bs4 import BeautifulSoup
import os
import common_function
import pandas as pd
import pdfplumber
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_fixed

def get_soup(url):
    global statusCode
    response = requests.get(url,headers=headers,stream=True)
    statusCode = response.status_code
    soup= BeautifulSoup(response.content, 'html.parser')
    return soup

def print_bordered_message(message):
    border_length = len(message) + 9
    border = "-" * (border_length - 2)

    print(f"+{border}+")
    print(f"| {message}...✍️ |")
    print(f"+{border}+")
    print()

def get_ordinal_suffix(n):
    if 11 <= n % 100 <= 13:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return str(n) + suffix

@retry(stop=stop_after_attempt(5), wait=wait_fixed(2))
def download_pdf(url, out_path,headers):
    with requests.get(url,headers=headers,stream=True) as r:
        r.raise_for_status()
        with open(out_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

def get_doi_page(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        first_page = pdf.pages[0]  # Get the first page (index 0)
        page_text = first_page.extract_text().split("\n")
        doi_tag = next((sin_text for sin_text in page_text if "doi.org/" in sin_text), None)
        doi = doi_tag.split("org/")[-1]
    return doi

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Priority": "u=0, i",
    "Sec-Ch-Ua": "\"Not/A)Brand\";v=\"8\", \"Chromium\";v=\"126\", \"Google Chrome\";v=\"126\"",
    "Sec-Ch-Ua-Arch": "\"x86\"",
    "Sec-Ch-Ua-Bitness": "\"64\"",
    "Sec-Ch-Ua-Full-Version": "\"126.0.6478.127\"",
    "Sec-Ch-Ua-Full-Version-List": "\"Not/A)Brand\";v=\"8.0.0.0\", \"Chromium\";v=\"126.0.6478.127\", \"Google Chrome\";v=\"126.0.6478.127\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Model": "\"\"",
    "Sec-Ch-Ua-Platform": "\"Windows\"",
    "Sec-Ch-Ua-Platform-Version": "\"15.0.0\"",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
}

duplicate_list = []
error_list = []
completed_list = []
attachment=None
url_id=None
current_date=None
current_time=None
Total_count=None
statusCode=None
Issue=Abstract=Volume=Year=Month=Day=DOI=Page_range=Identifier=Supplement=TOC_name=None
Article_type=Funding=Acknowledgement=Special=Part=Item_id=Publisher_item_type=None

Ref_value = "4311"
ini_path = os.path.join(os.getcwd(), "Info.ini")

try:
    with open('urlDetails.txt','r',encoding='utf-8') as file:
        url_list = file.read().strip().splitlines()
except Exception as error:
    Error_message = "Error in the \"urlDetails\" : " + str(error)
    print(Error_message)
    error_list.append(Error_message)
    common_function.attachment_for_email(url_id, duplicate_list, error_list, completed_list,
                                         len(completed_list),
                                         ini_path, attachment, current_date, current_time, Ref_value)

try:
    with open('completed.txt', 'r', encoding='utf-8') as read_file:
        read_content = read_file.read().split('\n')
except FileNotFoundError:
    with open('completed.txt', 'w', encoding='utf-8'):
        with open('completed.txt', 'r', encoding='utf-8') as read_file:
            read_content = read_file.read().split('\n')

url_index, url_check = 0, 0
while url_index < len(url_list):
    try:
        try:
            url, url_id = [item.strip() for item in url_list[url_index].split(',')]
        except Exception:
            raise Exception("There is an error in the urlDetails.txt file")

        current_datetime = datetime.now()
        current_date = str(current_datetime.date())
        current_time = current_datetime.strftime("%H:%M:%S")

        if url_check == 0:
            print_bordered_message("Scraping procedure will continue for ID:"+url_id)
            Download_Path, Email_Sent, Check_duplicate, user_id = common_function.read_ini_file(ini_path)
            current_out = common_function.return_current_outfolder(Download_Path, user_id, url_id)
            out_excel_file = common_function.output_excel_name(current_out)

        duplicate_list = []
        error_list = []
        completed_list=[]
        data = []
        attachment = None
        pdf_count = 1
        base_url = "http://intersections.anu.edu.au/"

        try:
            first_soup = get_soup(url)
            current_link = base_url+first_soup.find("a",string=re.compile(r"Issue"))["href"]
            current_soup = get_soup(current_link)
            if not current_soup:
                raise Exception("No matching issue link found.")
        except Exception:
            raise Exception("No matching issue link found.")

        try:
            main_text = current_soup.find(lambda tag:tag and tag.name == "font" and re.search(r"Issue\s*\d+",tag.get_text(strip=True))).get_text(strip=True)
            cleaned_text = re.sub(r"\s+", " ", main_text)

            issue_match = re.search(r"Issue\s*([\d–]+)", cleaned_text, re.IGNORECASE)
            year_match = re.search(r"[A-Za-z]+\s*(\d{4})", cleaned_text, re.IGNORECASE)
            month_match = re.search(r"([A-Za-z]+)\s*\d{4}", cleaned_text, re.IGNORECASE)

            Issue = issue_match.group(1) if issue_match else ""
            Year = year_match.group(1) if year_match else ""
            Month = month_match.group(1) if year_match else ""
        except Exception as e:
            Issue=Volume=Year=Month=None

        try:
            child_tag = current_soup.find("a",href=re.compile(r".pdf"))
            parent_tag = child_tag.find_parent("font",attrs={"face":"arial, helvetica, verdana, sans-serif","size":"-1"})
            All_articles = parent_tag.find_all("p",attrs={"style":"margin-left:1cm;text-indent:-1cm"})

            right_side_set = parent_tag.find_next("font",attrs={"face":"arial, helvetica, verdana, sans-serif","size":"-1"})
            All_articles.extend(right_side_set.find_all("p",attrs={"style":"margin-left:1cm;text-indent:-1cm"}))

            All_articles = list(filter(lambda link:link.find("a"),All_articles))

            if All_articles:
                Total_count=len(All_articles)
                print(f"✅ Total number of articles:{Total_count}","\n")
            else:
                raise Exception("No links found for articles")
        except Exception:
            raise Exception("No links found for articles")

        article_index, article_check = 0, 0
        while article_index < len(All_articles):
            Article_count = article_index+1
            Article_link, Article_title = None, None
            Art_index=All_articles[article_index]
            current_step = None
            try:
                current_step = "article link"
                article_link_tag = Art_index.find("a")
                Article_link = base_url+article_link_tag["href"]

                article_link_tag.decompose()

                current_step = "article title"
                article_title_tag = Art_index
                Article_title = re.sub(r"\s+"," ",article_title_tag.get_text())
                Article_title = Article_title.strip().replace(" reviewed by","")

                current_step = "pdf link"
                pdf_link = Article_link

                current_step = "pdf download"
                pdf_headers = {
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
                }
                output_fimeName = os.path.join(current_out, f"{pdf_count}.pdf")
                download_pdf(pdf_link, output_fimeName,pdf_headers)

                try:
                    DOI = get_doi_page(output_fimeName)
                except Exception:
                    DOI = None

                if article_check==0:
                    print("✅ "+get_ordinal_suffix(Article_count) + " article details have been scraped")

                current_step = "duplicate check"
                check_value, tpa_id = common_function.check_duplicate(DOI, Article_title, url_id, Volume, Issue)

                if Check_duplicate.lower() == "true" and check_value:
                    message = f"{Article_link} - duplicate record with TPAID : {tpa_id}"
                    duplicate_list.append(message)
                    print("📚 "+get_ordinal_suffix(Article_count)+" article is duplicated article" +"\n"+"➡️ "+"Article title:", Article_title+ '\n')
                    os.remove(output_fimeName)

                else:
                    current_step = "write excel"
                    data.append(
                        {
                            "Title": Article_title,
                            "DOI": DOI,
                            "Publisher Item Type": Publisher_item_type,
                            "ItemID": Item_id,
                            "Identifier": Identifier,
                            "Volume": Volume,
                            "Issue": Issue,
                            "Supplement": Supplement,
                            "Part": Part,
                            "Special Issue": Special,
                            "Page Range": Page_range,
                            "Month": Month,
                            "Day": Day,
                            "Year": Year,
                            "Article Type": Article_type,
                            "Abstract": Abstract,
                            "Funding": Funding,
                            "Acknowledgement": Acknowledgement,
                            "URL": Article_link,
                            "SOURCE File Name": f"{pdf_count}.pdf",
                            "user_id": user_id,
                            "TOC File Name": TOC_name
                        }
                    )

                    df = pd.DataFrame(data)
                    df.to_excel(out_excel_file, index=False)
                    pdf_count += 1
                    scrape_message = f"{Article_link}"
                    completed_list.append(scrape_message)
                    print("✅ "+get_ordinal_suffix(Article_count)+" article is original article" +"\n"+ "➡️ "+"Article title:", Article_title + '\n')

                if not Article_link in read_content:
                    with open('completed.txt', 'a', encoding='utf-8') as write_file:
                        write_file.write(Article_link + '\n')

                article_index, article_check = article_index + 1, 0

            except Exception as error:
                if article_check < 10:
                    article_check += 1
                else:
                    message = f"{Article_link} - Error in {current_step} for {Article_title} : [{str(error)}]"
                    print("❌ "+get_ordinal_suffix(Article_count)+" article could not be downloaded due to an error"+"\n"+"➡️ "+"Article title:", str(Article_title)+ '\n')
                    error_list.append(message)
                    article_index, article_check = article_index + 1, 0

        for attempt in range(10):
            try:
                common_function.sendCountAsPost(url_id, Ref_value, str(Total_count), str(len(completed_list)),str(len(duplicate_list)), str(len(error_list)))
                break
            except Exception as error:
                if attempt == 9:
                    error_list.append(f"Failed to send post request : {str(error)}")

        try:
            if str(Email_Sent).lower() == "true":
                attachment_path = out_excel_file
                if os.path.isfile(attachment_path):
                    attachment = attachment_path
                else:
                    attachment = None
                common_function.attachment_for_email(url_id, duplicate_list, error_list, completed_list,
                                                     len(completed_list), ini_path, attachment, current_date,
                                                     current_time, Ref_value)
            else:
                common_function.email_body_html(current_date, current_time, duplicate_list, error_list,
                                                completed_list,
                                                len(completed_list), url_id, Ref_value, attachment, current_out)
        except Exception as error:
            message = f"Failed to send email : {str(error)}"
            common_function.email_body_html(current_date, current_time, duplicate_list, error_list,
                                            completed_list,
                                            len(completed_list), url_id, Ref_value, attachment, current_out)

        sts_file_path = os.path.join(current_out, 'Completed.sts')
        with open(sts_file_path, 'w') as sts_file:
            pass
        print_bordered_message("Scraping has been successfully completed for ID:" + url_id)

        url_index, url_check = url_index + 1, 0
    except Exception as error:
        if url_check < 10:
            url_check += 1
        else:
            try:
                url_index, url_check = url_index + 1, 0
                error_messages = {
                    200: "Server error: Unable to find HTML content",
                    400: "Error in the site: 400 Bad Request",
                    401: "Error in the site: 401 Unauthorized",
                    403: "Error in the site: Error 403 Forbidden",
                    404: "Error in the site: 404 Page not found!",
                    408: "Error in the site: Error 408 Request Timeout",
                    500: "Error in the site: Error 500 Internal Server Error",
                    526: "Error in the site: Error 526 Invalid SSL certificate"
                }
                Error_message = error_messages.get(statusCode)

                if statusCode == 200 and str(error):
                    Error_message = "Error in the site: " + str(error)

                if Error_message is None:
                    Error_message = "Error in the site: " + str(error)

                print("❌ " + Error_message,"\n")
                error_list.append(Error_message)
                common_function.attachment_for_email(url_id, duplicate_list, error_list, completed_list,
                                                     len(completed_list),
                                                     ini_path, attachment, current_date, current_time, Ref_value)

            except Exception as error:
                message = f"Failed to send email : {str(error)}"
                print(message)
                common_function.email_body_html(current_date, current_time, duplicate_list, error_list, completed_list,
                                                len(completed_list), url_id, Ref_value, attachment, current_out)
                error_list.append(message)