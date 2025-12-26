import os.path

import requests
from bs4 import BeautifulSoup

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "Cache-Control": "max-age=0",
    "Priority": "u=0, i",
    "Sec-Ch-Ua": "\"Not/A)Brand\";v=\"8\", \"Chromium\";v=\"126\", \"Google Chrome\";v=\"126\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "\"Windows\"",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
}

def fetch_html(url):
    response = requests.get(url,headers=headers)
    response.raise_for_status()
    return response.content

def html_content(toc_html,html_contents):
    combined_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Combined HTML</title>
    </head>
    <body>
    """

    for content in html_contents:
        body = content.find('body')
        combined_html += str(body) + "<br>"

    combined_html += """
    </body>
    </html>
    """

    with open(toc_html, 'w', encoding='utf-8') as file:
        file.write(combined_html)

def get_toc_html(current_out,TOC_name,languageList):
    html_contents = languageList
    out_html=os.path.join(current_out,TOC_name)
    html_content(out_html, html_contents)
