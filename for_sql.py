import json
import os
import os.path
import requests
import sys
import csv
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.parse import urlencode
#from database import *
import secrets # Go to secret_data_sample.py and follow the instructions!
import sqlite3
CLIENT_ID = secrets.Client_ID
SEARCH_LIMIT = 41
api_key= secrets.api_key


# API constants, you shouldn't have to change these.
API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'

BUSINESS_PATH = '/v3/businesses/{id}'  # id: Business ID
REVIEW_PATH = BUSINESS_PATH + '/reviews' # inside BUSINESS_PATH, id: Business ID


def request(host, path, api_key, url_params=None):
    """Given your API_KEY, send a GET request to the API.
    Args:
        host (str): The domain host of the API.
        path (str): The path of the API after the domain.
        API_KEY (str): Your API Key.
        url_params (dict): An optional set of query parameters in the request.
    Returns:
        dict: The JSON response from the request.
    Raises:
        HTTPError: An error occurs from the HTTP request.
    """
    url_params = url_params or {}
    url = '{0}{1}'.format(host, quote(path.encode('utf8')))
    headers = {
        'Authorization': 'Bearer %s' % api_key,
    }

    print(u'Querying {0} ...'.format(url))
    
    response = requests.request('GET', url, headers=headers, params=url_params)

    return response.json()


def search_api(api_key, location = "Ann Arbor", term = "restaurants", limit = SEARCH_LIMIT):
    """Query the Search API by a search term and location. The result is sorted by weighted rating.

    Args:
        location (str): The search location passed to the API. By default, it's Ann Arbor.
        term (str): The search key word passed to the API. By default, it's restaurants.
        limit: The maximum of number of results returned by API is 50.
        
    Returns:
        dict: The JSON response from the request. Sorted by adjusted rating.
    """
    params = {
        'location': location,
        'term': term,
        'limit':limit,
        'sort_by': 'rating'    
    }

    return request(API_HOST, SEARCH_PATH, api_key, url_params = params)








def reviews_api(api_key, id):
    """Query the Reviews API by business id.

        Args:
            bearer_token: can be obtained by above function: obtain_bearer_token(host, path)
            id: Business ID can be found from search API.
            
        Returns:
            dict: The JSON response from the request. Include up to 3 reviews.
    """
    
    review_full_path = REVIEW_PATH.format(id = id) 
    return request(API_HOST, review_full_path, api_key)


def open_cache(cache_file_name):
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(cache_file_name, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict

  



#-------------------------------------------------------------------------------
# CACHE FUNCTION SETUP
#-------------------------------------------------------------------------------
# Set Cache Functions: Writing data to cache file.
def set_in_cache(cache_dict, cache_file_name):
    """ This is a general function can be used to write any cached data onto any files user specifies.
    
    Args:
       dict_data: to be cached data. Should be a dictionary.
       cache_file_name: the name of the file user wants to write on.
    
    Returns:
       dict_data itself
    
    Modifies:
       Upon execute, this will write data on the cache file.
    
    """
    print("Setting cache file in {}...".format(cache_file_name))
    
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(cache_file_name,"w")
    fw.write(dumped_json_cache)
    fw.close()
    return cache_dict


BASE_URL = 'https://api.yelp.com/v3/businesses/search'
def make_request_using_cache(url_params,key):
    unique_ident = key
    headers = {'Authorization': 'Bearer %s' % secrets.api_key,}
    if unique_ident in CACHE_DICTION:
        # print("Getting cached data...")
        return CACHE_DICTION[unique_ident]
    else:
        # print("Making a request for new data...")
        resp = requests.request('GET', BASE_URL, headers=headers, params=url_params)
        CACHE_DICTION[unique_ident] = resp.json()
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close()
        return CACHE_DICTION[unique_ident]

def yelp_search(location = "Chicago", term = "restaurants", limit = SEARCH_LIMIT):
    url_params = {
        'location': location,
        'term': term,
        'limit':limit,
        'sort_by': 'rating'   
    }
    key = '{}+{}'.format(term,location)
    return make_request_using_cache(url_params,key)


def reviews_in_cache(cache,api_key):
    ids = []
    #print(cache)
    print(cache)
    businesses = cache["businesses"]
    for business in businesses:
        ids.append(business["id"])
    # get the data using CREDS_DICTION and ids
    review_result = {} # a dictionary with key = restaurant_id, value = a list of up to 3 reviews.
    for id in ids:
        if id in REVIEWS_DICTION:
            review_result[id] = REVIEWS_DICTION[id]
            continue
        review_list = []
        result = reviews_api(api_key, id) # search that restaurant's review
        for one_review in result["reviews"]:
            review_list.append(one_review["text"]) # extract only the text part and append it to review_list for that restaurant
        review_result[id] = review_list # save it into review_result
    data_diction = set_in_cache(cache_dict = review_result, cache_file_name =REVIEWS_FNAME )
    return data_diction    













# Get data from cache file or API
def get_data(cache_file_name, identifier = "restaurants",  cache = None):
    """ If the data is in the cache file, retrieve from the corresponding cache file, otherwise retrieve data
    from API and set the data into cache file. The function also allows to refresh the search result by setting refresh to "Yes".
    
    Args:
       identifier: the data you want to get. It can be "credentials" or "restaurants" or "reviews". By default, it will get restuarants data.
       cache_file_name: the name of the cache file
       refresh: whether to refresh searching the data. If set to "Yes", it will wipe out the cached file and retrieve the data
                from API and save the new data into the cache file.
       credential: if identifier is "restaurants" or "reviews", you must supply credential
       cache: if identifier is "reviews", you must supply credential
    
    Returns:
       data_diction: cached data as a dictionary
    
    Modifies:
       If the data is not in the cache file, it will be written onto the cache file.
    
    """ 
    if (identifier not in ( "restaurants", "reviews")):
        print("**Error: identifier not accepted in function get_data()")
        exit()
    
    if(identifier == "restaurants"): 
        # get the data
        print("Getting data from Search APIs...")
        data_diction = yelp_search()
        #print(data)
        #search_result = search_api(api_key)
        # set in cache file
        #data_diction = set_in_cache(cache_dict = search_result, cache_file_name = cache_file_name)
        
    if(identifier == "reviews"):
        # sanitory check for availability of credentials' data and restaurant data
        if  not cache:
            print ("**Error: Obtain your credentials and restaurants data first and retreive reviews data.")
            exit() 
        # save all restaurant id in list
        print("Getting data from Review APIs, please wait...")
        print(cache)
        data_diction = reviews_in_cache(cache,api_key)
    else:
         print ("**Error: Bad value for refresh parameter in function get_data()")
                 
        
    return data_diction
    






    
#-------------------------------------------------------------------------------
# Write CSV Files
#-------------------------------------------------------------------------------
def write_restaurants_file(restaurants_list, filename):
    """Write the restaurants' informatino on csv file

        Args:
            restaurants_list: a list of restaurants, with each item represented by Restaurant object
            filename: the file to be writte on
            
        Returns:
            None
       
        Modifies:
            the file with filename
    """
    with open(filename,"w") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["restaurant_id", "restaurant_name", "categories", "price_level", "ratings", "review_counts", "state", "city", "street_address", "latitude", "longitude"])
        
        for restaurant in restaurants_list:
            csv_writer.writerow([restaurant.id, restaurant.name, restaurant.categories, restaurant.price, restaurant.ratings, restaurant.review_counts, restaurant.state, restaurant.city, 
            restaurant.street_address, restaurant.latitude, restaurant.longitude])
            
    print ("Writing restaurants'information on {}...".format(filename))


def write_reviews_file(reviews_dict, filename):
    """Write the restaurants' informatino on csv file

        Args:
            reviews_dict: a dictionary of reviews, with each item represented by key = restaurant_id, value = list of reviews
            filename: the file to be writte on
            
        Returns:
            None
       
        Modifies:
            the file with filename
    """
    with open(filename,"w") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["restaurant_id", "review_1", "review_2", "review_3"])
        
        for item in reviews_dict:
            reviews_list = reviews_dict[item]
            csv_writer.writerow([item, reviews_list[0], reviews_list[1], reviews_list[2]])
            
    print ("Writing restaurants' reviews on {}...".format(filename))
    




           
#-------------------------------------------------------------------------------
# Class Definition
#-------------------------------------------------------------------------------
class Restaurant(object):
    def __init__(self, rest_obj):
        self.id = rest_obj["id"]
        self.name = rest_obj["name"]
        self.categories = [] # a restaurant can have multiple categories
        for item in rest_obj["categories"]:
            self.categories.append(item["title"]) 
        if 'price' in rest_obj and rest_obj["price"] != '':
            self.price = rest_obj["price"]
        else:
            self.price = '$'
        #self.price = rest_obj["price"] if rest_obj["price"] != '' else '$'
        #print(self.price)
        self.ratings = rest_obj["rating"]
        self.review_counts = rest_obj["review_count"]
        self.state = rest_obj["location"]["state"]
        self.city = rest_obj["location"]["city"]
        self.street_address = rest_obj["location"]["address1"]
        self.latitude = rest_obj["coordinates"]["latitude"]
        self.longitude = rest_obj["coordinates"]["longitude"]
        
    
    def __repr__(self):
        return "<A Restaurant Object: 'name':{}, 'price':{}, ratings: {}, city: {}, address:{}>".format(self.name, self.price, self.ratings, self.city, self.street_address)
        
    
    def __contains__(self, name):
        return name in self.name
               

#-------------------------------------------------------------------------------
# Main Function
#-------------------------------------------------------------------------------

#if __name__ == '__main__':
print ("**Process started**")

# Check if client_id and client_secret has been filled
# if not CLIENT_ID or not CLIENT_SECRET:
#     print("Please provide Client ID and Client SECRET in secret_data_sample.py")
#     exit()


# Set up for cache file name
#CREDS_CACHE_FNAME = "creds.json" # a cache file to save the credentials, ie, all the tokens
CACHE_FNAME = "cache_contents.json" # a cache file to save the returned data on Ann Arbor's restaurants
REVIEWS_FNAME = "reviews.json" # a cache file to save the reviews on Ann Arbor's restaurants

CACHE_DICTION = open_cache(CACHE_FNAME)

REVIEWS_DICTION = open_cache(REVIEWS_FNAME)







# Get credentials data, restaurants data and reviews data
#CREDS_DICTION = get_data(CREDS_CACHE_FNAME, identifier = "credentials", refresh = "Yes") # a python dictionary to store credential data

CACHE_DICTION = get_data(CACHE_FNAME, identifier = "restaurants") # a python dictionary to store  restaurants data
#print(CACHE_DICTION)
REVIEWS_DICTION = get_data(REVIEWS_FNAME, identifier = "reviews", cache = CACHE_DICTION) # a python dictionary to store reviews data 


# Create restaurant object for each restaurant retrieved in CACHE_DICTION, and save all in a list
ann_arbor_restaurants = []
businesses = CACHE_DICTION["businesses"]
for business in businesses:
    rest_obj = Restaurant(business)
    ann_arbor_restaurants.append(rest_obj)


# Write each restaurant's information on restaurants.csv file
REST_CSV_FNAME = "restaurants.csv"
write_restaurants_file(restaurants_list = ann_arbor_restaurants, filename = REST_CSV_FNAME)

# Write each restaurant's reviews on reviews.csv file
REV_CSV_FNAME = "reviews.csv"
write_reviews_file(reviews_dict = REVIEWS_DICTION, filename = REV_CSV_FNAME)


DBNAME = "Final_Project.sqlite"

def init_tables():
    # Create db
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    try:
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
    except:
        print("Fail to connect to the database.")

    # Drop tables if they exist
    statement = '''
        DROP TABLE IF EXISTS 'Restaurants';
    '''
    cur.execute(statement)
    conn.commit()

    statement = '''
        DROP TABLE IF EXISTS 'PriceLevel';
    '''
    cur.execute(statement)
    conn.commit()

    statement = '''
        DROP TABLE IF EXISTS 'Reviews';
    '''
    cur.execute(statement)
    conn.commit()



    statement = '''
            CREATE TABLE "PriceLevel" (
                'Id' INTEGER PRIMARY KEY AUTOINCREMENT, 
                "price_level" VARCHAR(50) NOT NULL UNIQUE
            );
        '''
    try:
        cur.execute(statement)
    except:
        print("Fail to create table.")
    conn.commit()


    statement = '''
            CREATE TABLE "Reviews" (
                'Id' INTEGER PRIMARY KEY AUTOINCREMENT, 
                "review_1" TEXT NOT NULL UNIQUE, 
                "review_2" TEXT NOT NULL UNIQUE, 
                "review_3" TEXT NOT NULL UNIQUE
            );
            
        '''
    try:
        cur.execute(statement)
    except:
        print("Fail to create table.")
    conn.commit()

    # statement = '''
    #         CREATE TABLE "Restaurants" (
    #             'Id' INTEGER PRIMARY KEY AUTOINCREMENT, 
    #             "restaurant_name" TEXT NOT NULL UNIQUE,
    #             "categories" VARCHAR(300) NOT NULL,
    #             "price_level_id" INTEGER , 
    #             "ratings" REAL NOT NULL, 
    #             "review_count" INTEGER NOT NULL, 
    #             "longitude" REAL NOT NULL,
    #             "latitude" REAL NOT NULL,
    #             "review_id" INTEGER
    #         );
    #     '''
    

    statement = '''
            CREATE TABLE "Restaurants" (
                'Id' INTEGER PRIMARY KEY AUTOINCREMENT, 
                "restaurant_name" TEXT NOT NULL UNIQUE,
                "categories" TEXT NOT NULL,
                "price_level_id" INTEGER , 
                "ratings" REAL NOT NULL, 
                "review_count" INTEGER NOT NULL, 
                "longitude" REAL NOT NULL,
                "latitude" REAL NOT NULL,
                "review_id" INTEGER
            );
        '''
    try:
        cur.execute(statement)
    except:
        print("Fail to create table.")
    conn.commit()
    conn.close()

#def insert_data_price():
    



def get_restaurant_dict(rest_obj, price_level_dict, review_id):
    """ This helper function will convert Restaurant Object into a restaurant dictionanry that can be passed into
    insert() function in order to be inserted into the database.
    
    Args:
      rest_obj: A Restaurant object
      price_leve_dict: A python dictionary that stores eg. key = "$", value = "price_level_id" (many to one)
      review_id: rest_obj's corresponding review id in the Table Reviews
    
    Returns:
      A dictionary that can be passed into insert(). Keys are matched with the table Restaurant column names
    """
    rest_dict = {}
    rest_dict["restaurant_name"] = rest_obj.name
    rest_dict["categories"] = "/".join(rest_obj.categories)
    rest_dict["price_level_id"] = price_level_dict[rest_obj.price]
    rest_dict["ratings"] = rest_obj.ratings
    rest_dict["review_count"] = rest_obj.review_counts
    rest_dict["longitude"] = rest_obj.longitude
    rest_dict["latitude"] = rest_obj.latitude
    rest_dict["review_id"] = review_id
    
    return rest_dict

def get_reviews_dict(review_list):
        review_dict = {}
        review_dict["review_1"] = review_list[0]
        review_dict["review_2"] = review_list[1]
        review_dict["review_3"] = review_list[2]
        return review_dict



init_tables()
#insert_data_price()

try:
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
except:
    print("Fail to connect to the initial database.")


price_level_list = ["$", "$$", "$$$", "$$$$"]
price_level_id = {} # a python dictionary that stores eg. key = "$", value = "price_level_id"
print ("Inserting to Table PriceLevel...")
for price in price_level_list:
    price_dict = {}
    price_dict["price_level"] = price

    insertion = (None,price)
    statement = '''
        INSERT INTO PriceLevel
        VALUES (?,?)
    '''
    cur.execute(statement,insertion)

    statement = 'SELECT Id FROM PriceLevel ORDER BY Id DESC'
    cur.execute(statement)
    res = cur.fetchone()[0]
    price_level_id[price] = res
    
    
    #res = cur.fetchone()
    
    #print(res)
    #price_level_id[price] = 
    #price_level_id[price] = (conn.cursor.fetchone()["id"])
    
#print(price_level_id)
#for key in price_level_list:
    
    
    
    

#print(statement)

conn.commit()

#def insert_res(rest_list):
for restaurant in ann_arbor_restaurants:
    review_dict = get_reviews_dict(REVIEWS_DICTION[restaurant.id])
    #reviews_id = 
    try:
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
    except:
        print("Fail to connect to the initial database.")
    
    insertion = (None,review_dict["review_1"],review_dict["review_2"],review_dict["review_3"])
    #print(insertion)
    statement = '''
    INSERT INTO Reviews
    VALUES (?,?,?,?)
    '''
    
    cur.execute(statement,insertion)
    conn.commit()
    statement = 'SELECT Id FROM Reviews ORDER BY Id DESC'
    cur.execute(statement)
    res = cur.fetchall()
    cur.execute(statement)
    #res = cur.fetchone()
    review_id = int(res[0][0])
    #print(int(res[0][0]))
    rest_dict = get_restaurant_dict(restaurant, price_level_id, review_id)
    try:
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
    except:
        print("Fail to connect to the initial database.")

    # print(type(rest_dict["price_level_id"]))
    # print(type(rest_dict["review_id"]))
    # print(rest_dict["restaurant_name"] )
    # print(rest_dict["categories"] )
    # print(type(rest_dict["ratings"] ))
    # print(type(rest_dict["review_count"]))
    # print(type(rest_dict["longitude"]))
    # print(type(rest_dict["latitude"]))
   
    insertion = (None,rest_dict["restaurant_name"],rest_dict["categories"],rest_dict["price_level_id"],rest_dict["ratings"],rest_dict["review_count"],rest_dict["longitude"],rest_dict["latitude"],rest_dict["review_id"])
    statement = '''
    INSERT INTO Restaurants
    VALUES (?,?,?,?,?,?,?,?,?)
    '''
    cur.execute(statement,insertion)
    conn.commit()
print("Total Restaurants: ", CACHE_DICTION["total"])
print('----------------')
print('Process Completed!')
    
    

        
    
        

   

    












businesses': [{'id': 'UdO_uBm3sIM5DwaE8XIpbg', 'alias': 'grey-ghost-detroit-detroit', 'name': 'Grey Ghost Detroit', 'image_url': 'https://s3-media3.fl.yelpcdn.com/bphoto/ZZcxrXLceHFVnX4MY72ZHA/o.jpg', 'is_closed': False, 'url': 'https://www.yelp.com/biz/grey-ghost-detroit-detroit?adjust_creative=YpylRtCjjRIEyEtE5IUMwQ&utm_campaign=yelp_api_v3&utm_medium=api_v3_business_search&utm_source=YpylRtCjjRIEyEtE5IUMwQ', 'review_count': 683, 'categories': [{'alias': 'tradamerican', 'title': 'American (Traditional)'}, {'alias': 'beerbar', 'title': 'Beer Bar'}, {'alias': 'cocktailbars', 'title': 'Cocktail Bars'}], 'rating': 4.0, 'coordinates': {'latitude': 42.3451704384376, 'longitude': -83.0555171146989}, 'transactions': ['delivery'], 'price': '$$$', 'location': {'address1': '47 Watson St', 'address2': '', 'address3': None, 'city': 'Detroit', 'zip_code': '48201', 'country': 'US', 'state': 'MI', 'display_address': ['47 Watson St', 'Detroit, MI 48201']}, 'phone': '+13132626534', 'display_phone': '(313) 262-6534', 'distance': 3488.0998284615575}], 'total': 10, 'region': {'center': {'longitude': -83.09097290039062, 'latitude': 42.36241855567113}}, 'TRIP': '4.5'}, 






