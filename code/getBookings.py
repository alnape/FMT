#! /usr/bin/env python3.6
import argparse
import requests
import unicodecsv as csv

from bookingThread import BookingThread
from bs4 import BeautifulSoup
from fileWriter import FileWriter
from datetime import datetime, timedelta
#from time import time
import time

hotelsDict = []

rooms = 1
days = 1

def get_booking_page(session, offset, destination, checkInYear, checkInMonth, checkInDay, checkOutYear, checkOutMonth, checkOutDay):
    '''
    Make request to booking page and parse html
    :param offset:
    :return: html page
    '''

    url =  'https://www.booking.com/searchresults.es-es.html?' \
            'aid=303651&' \
            'label=gen173nr-1DCAEoggJCAlhYSDNYBGiTAYgBAZgBLsIBCndpbmRvd3MgMTDIAQzYAQPoAQGSAgF5qAID&' \
            'lang=es-es&' \
            'sid=a30fe61823d7891bf589ae78fb3317b2&sb=1&' \
            'error_url=https://www.booking.com/searchresults.en-gb.html&aid=304142&' \
            'sid=a30fe61823d7891bf589ae78fb3317b2&' \
            'tmpl=searchresults&' \
            'checkin_month={checkInMonth}&' \
            'checkin_monthday={checkInDay}&' \
            'checkin_year={checkInYear}&' \
            'checkout_month={checkOutMonth}&' \
            'checkout_monthday={checkOutDay}&' \
            'checkout_year={checkOutYear}&' \
            'class_interval=1&' \
            'from_sf=1&' \
            'genius_rate=1&' \
            'group_adults=2&' \
            'group_children=0&' \
            'label_click=undef&' \
            'no_rooms=1&' \
            'raw_dest_type=city&' \
            'room1=A%252CA&' \
            'rows=50&' \
            'sb_price_type=total&' \
            'shw_aparth=1&' \
            'slp_r_match=0&' \
            'src=searchresults&' \
            'src_elem=sb&' \
            'ss=Valencia&' \
            'ssb=empty&' \
            'ssne={destination}&' \
            'ssne_untouched={destination}&' \
            'ss_raw=valencia&' \
            'dest_id=-406131&dest_type=city&' \
            'iata=VLC&place_id_lat=39.469799&place_id_lon=-0.376542&' \
            'is_ski_area=0&' \
            'order=review_score_and_price&' \
            'offset={offset}'.format(offset=offset, destination=destination, \
                                    checkInYear=checkInYear, checkInMonth=checkInMonth, checkInDay=checkInDay, \
                                    checkOutYear=checkOutYear, checkOutMonth=checkOutMonth, checkOutDay=checkOutDay)
    
    #if offset == 0:
    #    print(url + '\n\n')

    #order=bayesian_review_score    'Mas valorado
    #order=review_score_and_price   'Puntuacion y precio
    #'raw_dest_type=country&' \
    #'aid=304142&' \
    #'ss=Valencia, Comunidad Valenciana, Espa%C3%B1a&' \
    r = requests.get(url, headers= {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/48.0'})
    html = r.content
    #parsed_html = BeautifulSoup(html, 'lxml')
    parsed_html = BeautifulSoup(html, 'html.parser')
    return parsed_html

def process_hotels(session, offset, advance, destination, CheckInYear, CheckInMonth, checkInDay, CheckOutYear, CheckOutMonth, checkOutDay):
    #print('Executing process_hotels with offset {%i}'%offset)   

    parsed_html = get_booking_page(session, offset, destination, CheckInYear, CheckInMonth, checkInDay, CheckOutYear, CheckOutMonth, checkOutDay)

    hotel = parsed_html.find_all('div', {'class': 'sr_item'})

    tot_hotels = parsed_html.select('h1')[0].text.strip()
    if offset == 0:
        print('Total properties: {%s}'%tot_hotels)

    checkInDate  = datetime.now() + timedelta(days=advance)
    checkOutDate = datetime.now() + timedelta(days=advance+1)
    checkIn  = checkInDate.strftime("%Y/%m/%d")
    checkOut = checkOutDate.strftime("%Y/%m/%d")

    for hot in hotel:
        propertyId = hot['data-hotelid']
        stars= hot['data-class']    
        score= hot['data-score']

        name = hot.find('span', {'class': 'sr-hotel__name'})
        name = name.text.strip('\n').replace(',','-') if name else 'NA'

        price = hot.find('div', {'class': 'bui-price-display__value prco-inline-block-maker-helper'})
        price = price.text.strip('\n') if price else 'NA'

        propertyType = hot.find('span', {'class': 'bui-badge bh-property-type'})
        propertyType = propertyType.text.strip('\n') if propertyType else 'NA'
        # if propertyType == 'NA':
        #     hot_url = hot.find('a', {'class': 'hotel_name_link url'})
        #     hot_url = hot_url['href'].strip('\n')
        #     hot_url = 'https://www.booking.com' + hot_url 

        #     r = requests.get(hot_url, headers= {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/48.0'})
        #     html = r.content
        #     parsed_html = BeautifulSoup(html, 'html.parser')
        #     propertyType = parsed_html.find('span', {'class': 'hp__hotel-type-badge'})
        #     propertyType = propertyType.text.strip('\n') if propertyType else 'NA'

        data = {'name': name, 
                'propertyId': propertyId, 
                'propertyType': propertyType,
                'city': destination, 
                'rooms': rooms, 
                'days': days,
                'price': price, 
                'checkIn': checkIn, 
                'checkOut': checkOut, 
                'stars': stars,
                'score': score,
                'advance': advance}
        hotelsDict.append(data)


def prep_data(advance=1, destination='Valencia', checkInYear=2019, checkInMonth=10, checkInDay=1, checkOutYear=2019, checkOutMonth=10, checkOutDay=2):
    '''
    Prepare data for saving
    :return: hotels: set()
    '''
    offset = 0    
    session = requests.Session()

    parsed_html = get_booking_page(session, offset, destination, checkInYear, checkInMonth, checkInDay, checkOutYear, checkOutMonth, checkOutDay)
    
    # To get last sr_pagination_item
    tot_pages = parsed_html.find_all('li', {'class': 'sr_pagination_item'})[-1].get_text().splitlines()[-1]
    print('Total scraped pages: {%i}'%int(tot_pages))
    # For testing
    #tot_pages = 2

    threads = []
    for i in range(int(tot_pages)):
        t = BookingThread(session, offset, advance, destination, checkInYear, checkInMonth, checkInDay, checkOutYear, checkOutMonth, checkOutDay, process_hotels)        
        threads.append(t)
        offset += 25
    for t in threads:
        t.start()        
    for t in threads:
        t.join()

    hotels_ = hotelsDict   
    print('Size hotels_: {%i}'%len(hotels_))
    
    return hotels_


def get_data(advance=1, destination='Valencia', checkInYear=2019, checkInMonth=10, checkInDay=1, checkOutYear=2019, checkOutMonth=10, checkOutDay=2):
    '''
    Get all accomodations in Valencia and save them in file
    :return: hotels-in-Valencia.csv file
    '''
    print('Preparing data...'+ datetime.now().strftime("%H:%M:%S"))
    hotels_list = prep_data(advance, destination, checkInYear, checkInMonth, checkInDay, checkOutYear, checkOutMonth, checkOutDay)
    print('Saving data...'+ datetime.now().strftime("%H:%M:%S"))
    save_data_csv(hotels_list, destination, advance)

def save_data_csv(data, destination, advance):
    today = datetime.now()   
    filename = ".\\data\\prices\\" + today.strftime("%Y%m%d") + '_' + today.strftime("%H%M%S") + '_Booking_' + destination + '_' + str(advance)  + '.csv'
    
    print (" Writing to output file <%s>..." %filename)
    with open(filename, 'wb') as csvfile:
        fieldnames = ['name', 'propertyId', 'propertyType', 'city', 'rooms', 'days', 'price', 'checkIn', 'checkOut', 'stars', 'score', 'advance']

        writer = csv.writer(csvfile)
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
            
        for row in data:
            writer.writerow(row)
        csvfile.close()
        print ("Process successfully finished !!!")


def save_data(data, out_format, destination):
    '''
    Saves hotels list in file
    :param data: hotels list
    :param out_format: json, csv or excel
    :return:
    '''
    writer = FileWriter(data, out_format, destination)
    file = writer.output_file()

    print('All accommodations are saved. You can find them in', file, 'file')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("advance", help='Number of days in advance.', default=1, type=int, nargs='?')
    parser.add_argument("destination", help='Destination to the booking request.', default='Valencia', nargs='?')
    args = parser.parse_args()

    checkInDate = datetime.now() + timedelta(days=args.advance)
    checkOutDate = datetime.now() + timedelta(days=args.advance+1)

    checkInYear = checkInDate.strftime("%Y")
    checkInMonth = checkInDate.strftime("%m")
    checkInDay = checkInDate.strftime("%d")
    checkOutYear = checkOutDate.strftime("%Y")
    checkOutMonth = checkOutDate.strftime("%m")
    checkOutDay = checkOutDate.strftime("%d")

    get_data(args.advance, args.destination, checkInYear, checkInMonth, checkInDay, checkOutYear, checkOutMonth, checkOutDay)
