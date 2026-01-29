import datetime
import os
import time
import base64
import requests
import logging
import random
import urllib.parse
from contextlib import contextmanager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchFrameException, ElementNotInteractableException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
import io

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

# Paramètres de recherche (Example)
prompt_user="Cyberpunk city with neon lights, detailed, 8k"
negat_user="blur, noisy, watermark"
style="Professional Photo"
resolution="Landscape"
nbimg="1"

def random_sleep(min_time: float = 1, max_time: float = 3):
    """Ajoute un délai aléatoire pour simuler un comportement humain."""
    time.sleep(random.uniform(min_time, max_time))

@contextmanager
def create_driver():
    """Context manager pour gérer le cycle de vie du driver."""
    driver = None
    try:
        options = Options()
        
        # Options pour masquer l'automatisation
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-infobars')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-extensions')
        
        # User agent personnalisé
        options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36')
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        yield driver
    finally:
        if driver:
            driver.quit()
            logging.info("Driver fermé.")

def safe_click(driver, element, max_attempts=3):
    """Tente de cliquer sur un élément de façon sûre avec plusieurs tentatives."""
    for attempt in range(max_attempts):
        try:
            if element.is_displayed() and element.is_enabled():
                element.click()
                return True
        except (StaleElementReferenceException, ElementNotInteractableException) as e:
            if attempt == max_attempts - 1:
                logging.error(f"Échec du clic après {max_attempts} tentatives: {str(e)}")
                return False
            random_sleep(1, 2)
            continue
    return False

def safe_set_textarea_value(driver, element, value):
    """Tente de définir la valeur d'un textarea/input de manière simple."""
    try:
        element.clear()
        random_sleep(0.5, 1)
        driver.execute_script("arguments[0].value = arguments[1];", element, value)
        element.send_keys(" ")
        element.send_keys("\b")
        return True
    except Exception as e:
        logging.error(f"Erreur lors de la modification du champ texte: {str(e)}")
        return False

def set_select_value(driver, select_element, value):
    """Définit la valeur d'un select en utilisant JavaScript."""
    try:
        driver.execute_script("""
            var select = arguments[0];
            var value = arguments[1];
            var opts = select.options;
            for(var opt, j = 0; opt = opts[j]; j++) {
                if(opt.text == value) {
                    select.selectedIndex = j;
                    select.dispatchEvent(new Event('change', { 'bubbles': true }));
                    break;
                }
            }
        """, select_element, value)
        return True
    except Exception as e:
        logging.error(f"Erreur lors de la sélection de l'option: {str(e)}")
        return False

def list_select_options(select_element):
    """Liste toutes les options d'un élément select."""
    options = []
    try:
        opts = select_element.find_elements(By.TAG_NAME, "option")
        for option in opts:
            options.append({
                'text': option.text,
                'value': option.get_attribute('value')
            })
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des options: {str(e)}")
    return options

def save_base64_image(base64_str, output_path):
    """Sauvegarde une image depuis sa représentation base64."""
    try:
        image_data = base64_str.split(',')[1]
        with open(output_path, 'wb') as f:
            f.write(base64.b64decode(image_data))
        return True
    except Exception as e:
        logging.error(f"Erreur lors de la sauvegarde de l'image: {str(e)}")
        return False

def wait_for_images(driver, timeout=120, expected_count=3):
    """Attend que les images soient chargées et vérifie leur contenu."""
    start_time = time.time()
    images = []
    time.sleep(5)
    
    while time.time() - start_time < timeout:
        try:
            output_area = driver.find_element(By.ID, "outputAreaEl")
            if output_area:
                image_divs = output_area.find_elements(By.CLASS_NAME, "t2i-image-ctn")
                if len(image_divs) >= expected_count:
                    current_images = []
                    for i, div in enumerate(image_divs[:expected_count], 1):
                        try:
                            driver.switch_to.default_content()
                            driver.switch_to.frame("outputIframeEl")
                            iframe = div.find_element(By.CLASS_NAME, "text-to-image-plugin-image-iframe")
                            driver.switch_to.frame(iframe)
                            try:
                                img = WebDriverWait(driver, 15).until(
                                    EC.presence_of_element_located((By.TAG_NAME, "img"))
                                )
                                src = img.get_attribute('src')
                                if src and src.startswith('data:image'):
                                    current_images.append(src)
                            except Exception:
                                pass
                            driver.switch_to.default_content()
                        except Exception:
                            driver.switch_to.default_content()
                            continue
                
                    if len(current_images) == expected_count:
                        return current_images
            time.sleep(2)
        except Exception:
            time.sleep(2)
    return images

def main():
    logging.info("Starting Perchance Scraper...")
    try:
        with create_driver() as driver:
            wait = WebDriverWait(driver, 60)
            driver.get("https://perchance.org/ai-text-to-image-generator") # Updated URL
            random_sleep(3, 5)

            # Cookie Banner
            try:
                agree_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.css-47sehv")))
                safe_click(driver, agree_button)
            except:
                pass

            # Switch to Iframe
            try:
                wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "outputIframeEl")))
            except:
                logging.error("Failed to switch to iframe")
                return

            # Find Inputs
            textareas = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "textarea")))
            if len(textareas) >= 2:
                safe_set_textarea_value(driver, textareas[1], prompt_user)
            
            # Click Generate
            generate_button = wait.until(EC.element_to_be_clickable((By.ID, "generateButtonEl")))
            if generate_button:
                safe_click(driver, generate_button)
                images = wait_for_images(driver, expected_count=int(nbimg))
                if images:
                    for i, img in enumerate(images):
                        save_base64_image(img, f"output_{i}.png")
                        logging.info(f"Image {i} saved.")
    except Exception as e:
        logging.error(f"Error: {e}")

if __name__ == "__main__":
    main()
