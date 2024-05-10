from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import configparser
from screeninfo import get_monitors
import pyotp
import time
import os
import sys
import platform
import logging
import schedule
import requests

#Setting base variables
isFirstPage = True

current_working_directory = os.getcwd()
current_working_directory += "\\" if platform.system() == "Windows" else "/"

#Initialize a logging file
log_path = current_working_directory + "dashboard.log"
logger = logging.getLogger("pwa_dashboard_logger")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('dashboard.log', mode='w')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.info(f"Log file created in: {current_working_directory}")

#Importing pyautogui or subprocess depending on Windows or Linux due to compatibility issues
logger.info("Detecting operating system compatibility")
if platform.system() == "Windows":
    import pyautogui
    import subprocess
    logger.info("Windows operating system detected, importing 'pyautogui & subprocess'...")
elif platform.system() == "Linux":
    import subprocess
    logger.info("Linux operating system detected, importing subprocess...")
    logger.info("Make sure XDOTools are installed!")
    print("When running on Linux make sure XDOTools is installed on the system!")
else:
    logger.error(f"No supported operating system detected, current operating system: {platform.system()}")

def update_program():
    subprocess.Popen(["python", "UpdateDashboardScript.py"]) if platform.system() == "Windows" else subprocess.Popen(["python3", "UpdateDashboardScript.py"])
    sys.exit(0)

def check_for_updates():
    response = requests.get("https://github.com/VoidCallerZ/Dashboard-Project/raw/main/version.txt")
    latest_version = response.text.strip()

    with open("version.txt", 'r') as f:
        current_version = f.read()
        
    if current_version < latest_version:
        print("A newer version is available. Updating...")
        update_program()
    else:
        print("Current version is up to date.")

#Initial update check
check_for_updates()

#ChromeOptions to disable all popups, from passwords to the automated tasks message
#Then start the Chrome webdriver with the set options
options = webdriver.ChromeOptions()
options.add_experimental_option("useAutomationExtension", False)
options.add_experimental_option("excludeSwitches", ['enable-automation'])
options.add_experimental_option("prefs", {"credentials_enable_service": False, "profile": {"password_manager_enabled": False}})
options.add_argument("--disable-infobars")
options.add_argument("--disable-notifications")
if platform.system() == "Linux":
    #options.add_argument(f"--user-data-dir={os.getcwd()}/foo")
    options.add_argument("remote-debugging-port=9222")
    options.binary_location = "/usr/bin/google-chrome"
driver = webdriver.Chrome(options=options)
logger.info("Started the Chrome webdriver...")

#Parse the config file to be used in code
def read_config(file_path='config.ini'):
    config = configparser.ConfigParser()
    config.read(file_path)
    return config

#Move the browser display to the given display ID
def move_browser_to_display(driver, display_id):
    monitors = get_monitors()

    # Check if the display ID is valid
    if 1 <= display_id <= len(monitors):
        display = monitors[display_id - 1]
        driver.set_window_position(display.x, display.y)
        print(f"Browser window moved to display {display_id} ({display.width}x{display.height})")
        logger.info(f"Browser window moved to display {display_id} ({display.width}x{display.height})")
    else:
        print(f"Invalid display ID: {display_id}")
        logger.error(f"Invalid display ID: {display_id}")

def verify_url(driver, url):
    get_url = driver.current_url
    if get_url == url:
        return True
    else:
        return False

#The main code to open and login each given page
#A value is given for the URL to load, the username and password to log in with and the monitor for the site to be displayed on
#If the MFA value is given, it will also use this to generate a OTP code to pass the MFA check on the site
def loginPage(url, username, password, monitor, mfa=None, outcomeUrl=None):
    logger.info("Starting loginPage function... ------------------------------")
    #Check if this is the first page or not, if it's not open a new window
    global isFirstPage
    if not isFirstPage:
        driver.switch_to.new_window('window')

    #Set the webpage URL
    driver.get(url)
    logger.info(f"Loading {url} ...")

    #Move the window to the correct display and enter fullscreen
    move_browser_to_display(driver, monitor)
    pyautogui.press('f11') if platform.system() == "Windows" else subprocess.run(["xdotool", "key", "F11"])

    #Wait for the actions above to be completed, then start looking for the username and password field
    driver.implicitly_wait(3)
    username_field = driver.find_element(By.XPATH, '//input[@type="text" or @type="email" or @type="username" or @id="loginInput"]')
    username_field.send_keys(username)

    try:
        driver.implicitly_wait(3)
        password_field = driver.find_element(By.XPATH, '//input[@type="password" or @id="password"]')
        password_field.send_keys(password)
    except:
        print("No password field found, searching for submit button...")
        logger.warning("No password field found, searching for submit button...")
        usernameSubmit = driver.find_element(By.XPATH, '//button[@type="submit"]')
        usernameSubmit.click()
        password_field = driver.find_element(By.XPATH, '//input[@type="password" or @id="password"]')
        password_field.send_keys(password)

    #Find and press the submit button
    try:
        driver.implicitly_wait(3)
        loginButton = driver.find_element(By.XPATH, '//button[@type="submit"]')
        loginButton.click()
    except:
        print("Login button not found, pressing enter!")
        logger.warning("Login button not found, pressing enter!")
        pyautogui.press('enter') if platform.system() == "Windows" else subprocess.run(["xdotool", "key", "KP_Enter"])

    #If MFA is required to log in the MFA value should be other than None
    #Grab the MFA key to generate an OTP code
    if mfa:
        logger.info("Entering MFA state, awaiting for page to be loaded...")
        time.sleep(10)
        secret_key = mfa
        totp = pyotp.TOTP(secret_key)
        otp = totp.now()
        logger.info(f"OTP Code: {otp}")

        #Find and fill the field for the OTP code
        driver.implicitly_wait(3)
        otpField = driver.find_element(By.XPATH, '//input[@type="text"]')
        otpField.send_keys(otp)

        #Find and press the submit button
        try:
            driver.implicitly_wait(3)
            logInButton = driver.find_element(By.XPATH, '//button[@type="submit"]')
            logInButton.click()
        except:
            print("Submit button not found, pressing enter!")
            logger.warning("Submit button not found, pressing enter!")
            pyautogui.press('enter') if platform.system() == "Windows" else subprocess.run(["xdotool", "key", "KP_Enter"])

    if outcomeUrl is not None:
        print("Checking if outcome URL is correct in 10 seconds...")
        logger.info("Checking if outcome URL is correct in 10 seconds...")
        time.sleep(10)
        if not verify_url(driver, outcomeUrl):
            print("Correct URL isn't loaded, retrying...")
            logger.warning("Correct URL isn't loaded, retrying...")
            isFirstPage = True
            loginPage(url, username, password, monitor, mfa, outcomeUrl)
        print("URL is correct, continuing...")
        logger.info("URL is correct, coninuing...")
    #Set the isFirstPage variable to False so a new window is opened for each recurring page
    isFirstPage = False
    logger.info("Ending loginPage function... ------------------------------")

#Refresh the given web page
def refresh_pages(window_handle):
    driver.switch_to.window(window_handle)
    driver.refresh()

def generate_default_config(config_path):
    comments = [
        "#Gemaakt door Rick Rasenberg - PWA B.V.",
        "#Onderstaand is het voorbeeld voor een webpagina\n",

        "#[PWA] - Dit is de naam voor deze websitesectie, deze heeft verder geen betekenis maar kan wel voor duidelijkheid zorgen",
        "#url = https://pwa.nl - De URL die moet worden geladen, zorg ervoor dat dit het inlogscherm is (verplicht)",
        "#username = Gebruiker - Gebruikersnaam van het account (verplicht)",
        "#password = Wachtwoord123 - Wachtwoord van het account (verplicht)",
        "#monitor = 1 - Monitornummer waar de pagina moet worden laten zien, identificeer hiervoor de monitoren (verplicht)",
        "#mfa = ABCDEFGHIJKLMN - De geheime sleutel om de MFA code te genereren (optioneel)",
        "#refreshInterval = 45 - Om de hoeveel minuten de pagina moet worden ververst om een timeout te voorkomen (optioneel)",
        "#outcome = https://pwa.nl/gelukt - De pagina waar het script op moet uitkomen, anders wordt dit opnieuw geprobeerd (optioneel)"
    ]

    with open(config_path, 'w') as configfile:
        configfile.write('\n'.join(comments))

def executeSingleCommand(key, value):
    match key:
        case "click_button":
            try:
                clickButton = driver.find_element(By.XPATH, f'//button[@type="{value}" or @id="{value}" or @class="{value}"]')
                clickButton.click()
            except NoSuchElementException:
                clickButton = driver.find_element(By.XPATH, f'//*[@type="{value}" or @id="{value}" or @class="{value}"]')
                clickButton.click()
            except:
                print(f"Button: {value} could not be found as type, id or class value!")
                logger.error(f"Button: {value} could not be found as type, id or class value!")
        case "select_field":
            try:
                fieldElement = driver.find_element(By.XPATH, f'//input[@type="{value}" or @id="{value}" or @class="{value}"]')
            except:
                print(f"Field: {value} could not be found as type, id or class value!")
                logger.error(f"Field: {value} could not be found as type, id or class value!")
        case "send_keys":
            try:
                fieldElement.send_keys(value)
            except:
                print(f"Could not fill in {value} for unknown reasons!")
                logger.error(f"Could not fill in {value} for unknown reasons!")
        case "goto_url":
            try:
                driver.get(value)
            except:
                print(f"Could not load the given URL: {value}!")
                logger.error(f"Could no load the given URL: {value}!")
        case "zoom_percentage":
            try:
                driver.execute_script(f"document.body.style.zoom='{value}%'")
            except:
                print(f"Could not zoom to: {value}%")
                logger.error(f"Could not zoom to: {value}%")
        case "press_key":
            try:
                pyautogui.press(value) if platform.system() == "Windows" else subprocess.run(["xdotool", "key", value])
            except:
                print(f"Key: {value} could not be pressed! Make sure they are available in: https://pyautogui.readthedocs.io/en/latest/keyboard.html#keyboard-keys")
                logger.error(f"Key: {value} could not be pressed! Make sure they are available in: https://pyautogui.readthedocs.io/en/latest/keyboard.html#keyboard-keys")
    time.sleep(5)

#VERSION
print("Dashboard.py running version 1.4")
print("Changes:\n=----------=\nAdded full Linux compatibiliy.\nAdded a log file showing a detailed output of the code.\nImproved code efficiency.\n=----------=")

#Schedule update check for every 4 hours
schedule.every(4).hours.do(check_for_updates)

#Get the values from the parsed config file
config_path = current_working_directory + "config.ini"
if not os.path.exists(config_path):
    print("No valid config file found, creating...")
    logger.warning(f"No valid config file found, creating file in: {current_working_directory}")
    generate_default_config(config_path)
    print("Config file created, please edit the config file and restart the program!")
    logger.warning(f"Config file created in {config_path}, please edit the config file and restart the program!")
    raise SystemExit

config = read_config(config_path)
logger.info("Config file read successfully!")

#For each section in the config get the url, username, password, monitor and mfa value
for website_section in [section for section in config.sections() if '.' not in section]:
    logger.info(f"Processing section: '{website_section}'...")
    url = config.get(website_section, 'url')
    username = config.get(website_section, 'username')
    password = config.get(website_section, 'password', raw=True)
    monitor = config.getint(website_section, 'monitor')
    mfa = config.get(website_section, 'mfa', fallback=None)
    outcomeUrl = config.get(website_section, 'outcome', fallback=None)
    refresh_interval = config.getint(website_section, 'refreshInterval', fallback=None)

    #Call the loginPage function to open and login the given webpages
    loginPage(url, username, password, monitor, mfa, outcomeUrl)

    #Get the current window handle for the refresh_pages() function
    window_handle = driver.window_handles[-1]
    config.set(website_section, 'window_handle', window_handle)
    logger.info(f"Window handle '{window_handle}' written to config file!")

    if refresh_interval is not None:
        schedule.every(refresh_interval).minutes.do(refresh_pages)

    [time.sleep(10)]
    for subsection in [subsection for subsection in config.sections() if subsection.startswith(website_section + '.')]:
        logger.info(f"Processing subsection: '{subsection}' for '{website_section}'...")
        for key, value in config.items(subsection):
            key_values = [item.strip() for item in value.split(', ')]

            for entry_value in key_values:
                executeSingleCommand(key, entry_value)

#Write the window handle in the config file
config.write(open('config.ini', 'w'))

#Try refreshing the pages once the rest of the script has completed, this will run until interrupted
print("Press CTRL + C to terminate the script.")
try:
    while True:
        schedule.run_pending()
        time.sleep(1)
except KeyboardInterrupt:
    print("Script interrupted by user")
    logger.info("Script interrupted by user")