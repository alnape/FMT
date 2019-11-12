#! /usr/bin/env python3.6
import argparse
import requests
import unicodecsv as csv

from bookingThread import BookingThread
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from time import time

hotelsDict = []

# By default
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
            'ss={destination}&' \
            'ssb=empty&' \
            'ssne={destination}&' \
            'ssne_untouched={destination}&' \
            'ss_raw={destination}&' \
            'dest_id=-406131&dest_type=city&' \
            'iata=VLC&place_id_lat=39.469799&place_id_lon=-0.376542&' \
            'is_ski_area=0&' \
            'order=review_score_and_price&' \
            'offset={offset}'.format(offset=offset, destination=destination, \
                                    checkInYear=checkInYear, checkInMonth=checkInMonth, checkInDay=checkInDay, \
                                    checkOutYear=checkOutYear, checkOutMonth=checkOutMonth, checkOutDay=checkOutDay)
    #print(url)
    r = requests.get(url, headers= {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/48.0'})
    html = r.content
    parsed_html = BeautifulSoup(html, 'html.parser')
    return parsed_html

def process_hotels(session, offset, advance, destination, CheckInYear, CheckInMonth, checkInDay, CheckOutYear, CheckOutMonth, checkOutDay):
    print('Executing process_hotels with offset {%i}'%offset)
    parsed_html = get_booking_page(session, offset, destination, CheckInYear, CheckInMonth, checkInDay, CheckOutYear, CheckOutMonth, checkOutDay)

    hotel = parsed_html.find_all('div', {'class': 'sr_item'})

    tot_hotels = parsed_html.select('h1')[0].text.strip()
    if offset == 0:
        print('Tot_hotels: {%s}'%tot_hotels)

    for hot in hotel:
        propertyId = hot['data-hotelid']
        name = hot.find('span', {'class': 'sr-hotel__name'})
        name = name.text.strip('\n').replace(',','-') if name else 'NA'

        propertyType = hot.find('span', {'class': 'bui-badge bh-property-type'})
        propertyType = propertyType.text.strip('\n') if propertyType else 'NA'
        if propertyType == 'NA':
            hot_url = hot.find('a', {'class': 'hotel_name_link url'})
            hot_url = hot_url['href'].strip('\n')
            hot_url = 'https://www.booking.com' + hot_url 

            r = requests.get(hot_url, headers= {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/48.0'})
            html = r.content
            parsed_html = BeautifulSoup(html, 'html.parser')
            propertyType = parsed_html.find('span', {'class': 'hp__hotel-type-badge'})
            propertyType = propertyType.text.strip('\n') if propertyType else 'NA'
            #print('{%s} {%s}'%(name, propertyType))

        address = hot.find('div', {'class': 'sr_card_address_line'})
        district = address.find('a').contents[0].strip('\n') if address else 'NA'
        coords = address.find('a')['data-coords'] if address else 'NA'
        #print('-------------------------------------------------------------------------------------')
        print('{%s} {%s} {%s}'%(propertyId, name, propertyType))

        data = {'propertyId': propertyId, 
                'propertyType': propertyType, 
                'district': district, 
                'coords': coords}
        hotelsDict.append(data)


def prep_data(destination='Valencia', checkInYear=2019, checkInMonth=10, checkInDay=1, checkOutYear=2019, checkOutMonth=10, checkOutDay=2):
    '''
    Prepare data for saving
    :return: hotels: set()
    '''
    offset = 0    
    session = requests.Session()

    parsed_html = get_booking_page(session, offset, destination, checkInYear, checkInMonth, checkInDay, checkOutYear, checkOutMonth, checkOutDay)
    
    # To get last sr_pagination_item
    tot_pages = parsed_html.find_all('li', {'class': 'sr_pagination_item'})[-1].get_text().splitlines()[-1]
    print('Total pages: {%i}'%int(tot_pages))
    # For testing
    #tot_pages = 2

    threads = []
    for i in range(int(tot_pages)):
        t = BookingThread(session, offset, 1, destination, checkInYear, checkInMonth, checkInDay, checkOutYear, checkOutMonth, checkOutDay, process_hotels)        
        threads.append(t)
        offset += 25
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    hotels_ = hotelsDict   
    print('Size hotels_: {%i}'%len(hotels_))
    
    return hotels_


def get_data(destination='Valencia', checkInYear=2019, checkInMonth=10, checkInDay=1, checkOutYear=2019, checkOutMonth=10, checkOutDay=2):
    '''
    Get all accomodations in Valencia and save them in file
    :return: csv file
    '''
    print('Preparing data...'+ datetime.now().strftime("%H:%M:%S"))
    hotels_list = prep_data(destination, checkInYear, checkInMonth, checkInDay, checkOutYear, checkOutMonth, checkOutDay)
    print('Saving data...'+ datetime.now().strftime("%H:%M:%S"))
    save_data_csv(hotels_list, destination)

def save_data_csv(data, destination):
    today = datetime.now()   
    filename = ".\\data\\properties\\" + today.strftime("%Y%m%d") + '_' + today.strftime("%H%M%S") + '_Booking_' + destination + '.csv'
    
    print (" Writing to output file <%s>..." %filename)
    with open(filename, 'wb') as csvfile:
        fieldnames = ['propertyId', 'propertyType', 'district', 'coords']

        writer = csv.writer(csvfile)
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
            
        for row in data:
            writer.writerow(row)
        csvfile.close()
        print ("Process successfully finished !!!")


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

    get_data(args.destination, checkInYear, checkInMonth, checkInDay, checkOutYear, checkOutMonth, checkOutDay)
