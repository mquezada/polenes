import requests
import bs4
import dateparser
import datetime
import time
import pandas as pd
import tqdm
import random


def get_page_contents(code) -> str | None:
    r = requests.get(base_url, params={"idgraf": code, "ciudad": 4, "framed": "yes"})
    s = r.text
    clean_text = s.encode('iso-8859-1').decode('utf-8')
    if "No hay aún registros en esta localidad" in clean_text:
        return None
    return clean_text



def get_date_period(page: str) -> tuple[datetime.date, datetime.date]: 
    ### we need to get the date period: jueves, 16 de noviembre de 2023 al miercoles, 22 de noviembre de 2023
    soup = bs4.BeautifulSoup(page, "html.parser")
    date_period = soup.find_all("p", class_="g-font-size-16 g-line-height-2")[0].text
    date_period = date_period.split(": ")[1]
    date_period = date_period.split(" al ")
    start_date = dateparser.parse(date_period[0]).date()
    end_date = dateparser.parse(date_period[1]).date()

    return start_date, end_date


def get_locality(page: str) -> str:  
    #### page looks like this:
    # <!-- Google tag (gtag.js) -->
    # <script async src="https://www.googletagmanager.com/gtag/js?id=G-KM6566SXZV"></script>
    # <script>
    #   window.dataLayer = window.dataLayer || [];
    #   function gtag(){dataLayer.push(arguments);}
    #   gtag('js', new Date());

    #   gtag('config', 'G-KM6566SXZV');
    # </script>
    # <div class="container g-py-20 g-pb-45 g-pb-45" style="background-image: url('assets/img/bg/bg-dienteleon.png'); background-repeat:repeat;">
    #   <section class="g-py-20">
    #     <div class="container">
    #       <header class="text-center g-width-80x--md mx-auto g-mb-70"> </header>
    #       <div class="u-heading-v6-2 text-center text-uppercase g-mb-20">
    #         <h2 class="h3 u-heading-v6__title g-brd-primary g-color-gray-dark-v2 g-font-weight-600">Promedios Semanales Las Condes</h2>
    #       </div>
    #       <div class="g-pos-rel g-z-index-1">
    #         <!-- Heading -->
            
    #         <div class="g-max-width-750 text-center mx-auto g-mb-10">
    #           <p class="g-font-size-16 g-line-height-2">PerÃ­odo: jueves, 16 de noviembre de 2023 al miÃ©rcoles, 22 de noviembre de 2023</p>
    #           <p class="g-font-size-13 g-line-height-2 g-font-weight-600">Niveles en granos de polen por m<sup>3</sup> de aire (g/m<sup>3</sup>).</p>
    
    #         </div>

    ### we need to get the locality: "Santiago"
    soup = bs4.BeautifulSoup(page, "html.parser")
    locality_desc = soup.find_all("h2", class_="h3 u-heading-v6__title g-brd-primary g-color-gray-dark-v2 g-font-weight-600")[0].text
    locality = " ".join(locality_desc.split(" ")[2:])
    return locality


def get_chart_values(page: str) -> list[int]:
    soup = bs4.BeautifulSoup(page, "html.parser")
    js_data = soup.find_all("script", language="javascript")[0].text
    # remove "//data" first
    js_data = js_data.split("//data")[1]
    js_data = js_data.split("data: [")[1]
    js_data = js_data.split("]")[0]
    js_data = js_data.split(", ")
    js_data = [int(x) for x in js_data]
    return js_data

def get_polen_values(page: str) -> list[int]:
    # there is a labels value in the script:
    #                 labels = [
    #                         'Total Arboles\n(77 g/m3)',
    #                         'Plátano Oriental\n(3 g/m3)',
    #                         'Pastos\n(21 g/m3)',
    #                         'Malezas\n(7 g/m3)'
    #                 ];

    # we want to extract the values in the parenthesis like this:
    # {'Total Arboles': 77, 'Plátano Oriental': 3, 'Pastos': 21, 'Malezas': 7}

    soup = bs4.BeautifulSoup(page, "html.parser")
    js_data = soup.find_all("script", language="javascript")[0].text
    # find Total Arboles
    js_data = js_data.split("Total Arboles")[1]
    js_data = js_data.split("];")[0]
    
    lines = [s.strip().replace("'", "") for s in js_data.split("\n")]
    values = []
    for line in lines:
        if line.strip() == "":
            continue

        tokens = line.split("\\n")
        # get value from tokens[1]
        value = int(tokens[1].split(" ")[0][1:])
        values.append(value)

    return values


labels = [
    "Total Árboles",
    "Plátano Oriental",
    "Pastos",
    "Malezas"
]


base_url = "http://polenes.cl/niveles.asp"  # &idgraf= ciudad=4 framed=yes
data = []
# start_code = 4231
# start_code = 4149

## 4231 -- 4058
## 4149 -- 4057
## 4057 -- 1013
## 1012 -- 0

# start_code = 1012

start_code = 4057
end_code = 1013
codes = range(start_code, end_code, -1)

for code in tqdm.tqdm(codes):
    # print(code)

    page = get_page_contents(code)
    if page is None:
        print(f"Skipping {code}")
        time.sleep((random.random()))
        continue

    start_date, end_date = get_date_period(page)
    # print("*", start_date, end_date)

    locality = get_locality(page)
    # print("*", locality)

    chart_values = get_chart_values(page)
    # print("*", chart_values)

    polen_values = get_polen_values(page)
    # print("*", polen_values)

    data.append((
        code,
        locality,
        start_date,
        end_date,
        chart_values[0],
        chart_values[1],
        chart_values[2],
        chart_values[3],
        polen_values[0],
        polen_values[1],
        polen_values[2],
        polen_values[3],
    ))
    time.sleep((random.random()))

df = pd.DataFrame(data, columns=["code", "locality", "start_date", "end_date", "chart_arboles", "chart_platano", "chart_pastos", "chart_malezas", "polen_arboles", "polen_platano", "polen_pastos", "polen_malezas"])

df.to_csv("polenes2.csv", index=False)


### R code

# library(tidyr)
# library(lubridate)
# library(dplyr)
# library(ggplot2)

# df <- read.csv("~/polen/polenes2.csv")
# df$date <- ymd(df$start_date)

# df$month <- month(df$date)
# df$year <- year(df$date)

# df$week <- isoweek(df$date)

# df2 <- df[!duplicated(df), ]

# df2 %>% 
#   filter(locality == "Santiago") %>% 
#   group_by(year, week) %>% 
#   summarise(
#     pasto = mean(polen_pastos)
#   ) %>% 
#   spread(year, pasto) %>%
#   write.csv("~/polen/spread.csv")

# df2 %>% 
#   filter(locality == "Santiago", year != 2002, year != 1999, week > 25) %>% 
#   mutate(year = factor(year)) %>%
#   group_by(year, week) %>% 
#   summarise(
#     pasto = mean(polen_pastos)
#   ) %>% 
#   ggplot(aes(x=week, y=pasto, group=year, color=year, shape=year)) + geom_point() + geom_smooth(se=F)