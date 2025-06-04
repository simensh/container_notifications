from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import requests
import json
import os
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

try:
    logging.info("Starter bolia.py...")
    # Din eksisterende kode her
except Exception as e:
    logging.error(f"En feil oppstod: {e}", exc_info=True)
    
def check_bolia_outlet(slack_webhook_url=None):
    # URL til Bolia Outlet
    url = "https://www.bolia.com/nb-no/mot-oss/butikker/online-outlet/?room=oppbevaring&lastfacet=room"
    
    # Produktnumre vi leter etter
    target_product_ids = ["04-009-21_00001", "04-009-21_00001"]  # Legg til de produktnumrene du vil søke etter

    # Konfigurer Selenium med ChromeDriver
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Kjør i headless-modus (uten GUI)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")  # Sett vindusstørrelse
    
    # Bruk den forhåndsinstallerte chromedriver
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    #driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)



    try:
        logging.info("Starter Selenium WebDriver...")
        logging.info("Selenium WebDriver startet.")
        # Åpne nettsiden
        driver.get(url)
        
        # Vent litt for å la siden laste fullstendig
        time.sleep(5)
        logging.info("Åpnet nettsiden.")
        # Bruk eksplisitt venting for å sikre at siden er lastet
        wait = WebDriverWait(driver, 20)
        
        # Vent til produktene er lastet
        try:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "c-product-tile__link")))
            print("Fant produktlenker!")
        except TimeoutException:
            print("Kunne ikke finne produktlenker, prøver å scrolle...")
            
            # Prøv å scrolle ned på siden for å laste inn flere produkter
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        # Ta skjermbilde for debugging
        driver.save_screenshot("bolia_debug.png")
        
        # Liste for å lagre matchende produkter
        matching_products = []
        
        # Søk etter produkter basert på produktnummer i article class
        for product_id in target_product_ids:
            try:
                # Finn article-elementer som inneholder produktnummeret
                articles = driver.find_elements(By.CSS_SELECTOR, f"article[class*='product-{product_id}']")
                print(f"Fant {len(articles)} artikler med produktnummer {product_id}")
                
                for article in articles:
                    # Finn produktlenken for å få tittel og URL
                    product_link = article.find_element(By.CSS_SELECTOR, ".c-product-tile__link")
                    product_name = product_link.get_attribute("title").strip()
                    product_url = product_link.get_attribute("href")
                    
                    # Hent HTML-koden for hele article-elementet
                    article_html = article.get_attribute('outerHTML')
                    
                    # Finn priser ved å søke direkte i HTML-koden
                    sales_price = "Salgspris ikke funnet"
                    list_price = "Listepris ikke funnet"
                    discount = "Rabatt ikke funnet"
                    
                    # Søk etter salgspris i HTML-koden
                    sales_price_match = re.search(r'salesPrice\.amount">([\d\s]+&nbsp;[\d\s]+\s*kr\.)', article_html)
                    if sales_price_match:
                        sales_price = sales_price_match.group(1).replace('&nbsp;', ' ')
                        print(f"Fant salgspris i HTML: {sales_price}")
                    
                    # Søk etter listepris i HTML-koden
                    list_price_match = re.search(r'listPrice\.amount">([\d\s]+&nbsp;[\d\s]+\s*kr\.)', article_html)
                    if list_price_match:
                        list_price = list_price_match.group(1).replace('&nbsp;', ' ')
                        print(f"Fant listepris i HTML: {list_price}")
                    
                    # Søk etter rabatt i HTML-koden
                    discount_match = re.search(r'Spar\s+(\d+%)', article_html)
                    if discount_match:
                        discount = f"Spar {discount_match.group(1)}"
                        print(f"Fant rabatt i HTML: {discount}")
                    
                    # Finn produktdetaljer
                    details = "Detaljer ikke funnet"
                    details_match = re.search(r'product\.details">(.*?)<', article_html)
                    if details_match:
                        details = details_match.group(1)
                        print(f"Fant detaljer i HTML: {details}")
                    
                    # Legg til i listen over matchende produkter
                    matching_products.append({
                        "navn": product_name,
                        "url": product_url,
                        "produktnummer": product_id,
                        "salgspris": sales_price,
                        "listepris": list_price,
                        "rabatt": discount,
                        "detaljer": details
                    })
                    print(f"Fant matchende produkt: {product_name} med nummer {product_id}")
            except Exception as e:
                print(f"Feil ved søk etter produktnummer {product_id}: {e}")
        
        # Forbered resultatene
        if matching_products:
            # Lag en tekstversjon for konsoll-output
            text_result = "Produkter funnet:\n"
            for product in matching_products:
                text_result += f"Navn: {product['navn']}\n"
                text_result += f"URL: {product['url']}\n"
                text_result += f"Produktnummer: {product['produktnummer']}\n"
                text_result += f"Salgspris: {product['salgspris']}\n"
                text_result += f"Listepris: {product['listepris']}\n"
                text_result += f"Rabatt: {product['rabatt']}\n"
                text_result += f"Detaljer: {product['detaljer']}\n"
                text_result += "-------------------\n"
            
            # Send til Slack hvis webhook URL er angitt
            if slack_webhook_url:
                send_to_slack(matching_products, slack_webhook_url)
            
            return text_result
        else:
            message = f"Ingen produkter med produktnumrene {', '.join(target_product_ids)} ble funnet."
            
            # Send til Slack hvis webhook URL er angitt
            #if slack_webhook_url:
            #    send_to_slack_message(message, slack_webhook_url)
            
            return message + " Sjekk bolia_debug.png for å se hvordan siden ser ut."

    except Exception as e:
        error_message = f"En feil oppstod: {e}"
        
        # Send feilmelding til Slack hvis webhook URL er angitt
        if slack_webhook_url:
            send_to_slack_message(error_message, slack_webhook_url)
        
        return error_message

    finally:
        # Lukk nettleseren
        driver.quit()
        logging.info("Avsluttet Selenium.")

def send_to_slack(products, webhook_url):
    """
    Send produktinformasjon til Slack via webhook
    """
    # Lag en pen formatert melding for Slack
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🛋️ Bolia Outlet - Produktoppdatering",
                "emoji": True
            }
        },
        {
            "type": "divider"
        }
    ]
    
    # Legg til hvert produkt som en seksjon
    for product in products:
        product_block = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*<{product['url']}|{product['navn']}>*\n"
                        f"Salgspris: *{product['salgspris']}*\n"
                        f"Listepris: ~{product['listepris']}~\n"
                        f"{product['rabatt']}\n"
                        f"Detaljer: {product['detaljer']}"
            }
        }
        blocks.append(product_block)
        blocks.append({"type": "divider"})
    
    # Legg til tidsstempel
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"Oppdatert: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            }
        ]
    })
    
    # Lag payload for Slack
    payload = {
        "blocks": blocks
    }
    
    # Send til Slack
    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        print(f"Melding sendt til Slack, status: {response.status_code}")
    except Exception as e:
        print(f"Feil ved sending til Slack: {e}")

def send_to_slack_message(message, webhook_url):
    """
    Send en enkel tekstmelding til Slack via webhook
    """
    payload = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🛋️ *Bolia Outlet Oppdatering*\n{message}"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Oppdatert: {time.strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        print(f"Melding sendt til Slack, status: {response.status_code}")
    except Exception as e:
        print(f"Feil ved sending til Slack: {e}")

# Test funksjonen lokalt
if __name__ == "__main__":
    # Sett inn din Slack webhook URL her
    slack_webhook_url = os.environ.get("slack-webhook-url")
    
    # Hvis du ikke vil sende til Slack under testing, kan du sette URL til None
    # slack_webhook_url = None
    
    result = check_bolia_outlet(slack_webhook_url)
    print(result)
