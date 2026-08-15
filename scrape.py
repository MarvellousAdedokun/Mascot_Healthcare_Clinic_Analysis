from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

# As there are possibilities of different chrome
# browser and we are not sure under which it get
# executed let us use the below syntax
driver = webdriver.Chrome(ChromeDriverManager().install())