import json
import os
import os.path
import requests
import sys
import csv
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.parse import urlencode
import secrets 
import sqlite3
from bs4 import BeautifulSoup
import plotly.graph_objs as go
from plotly.offline import plot



api_key= secrets.api_key


# API constants
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



def make_request_using_cache(url_params,key):
    unique_ident = key
    headers = {'Authorization': 'Bearer %s' % secrets.api_key,}
    if unique_ident in CACHE_DICTION:
        print("Getting cached data  of the information from the yelp...")
        return CACHE_DICTION[unique_ident]
    else:
        print("Making a request for new data...")
        resp = requests.request('GET', API_HOST+SEARCH_PATH, headers=headers, params=url_params)
        CACHE_DICTION[unique_ident] = resp.json()
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close()
        return CACHE_DICTION[unique_ident]

def yelp_search(location = "Detroit", term = "restaurants", limit = 1):
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
    businesses = []
    for b in cache:
        for b2 in b["businesses"]:
            ids.append(b2['id'])
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
        if len(review_list) < 3:
            review_list.append('Need more reviews')
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
    
    
    """ 
    # if (identifier not in ( "restaurants", "reviews")):
    #     print("**Error: identifier not accepted in function get_data()")
    #     exit()
    data_diction = []
    if(identifier == "restaurants"): 
        # get the data
        print("Getting data from Search APIs...")
        for res in top_restaurants:
            if yelp_search(term =res)['businesses'] != []:
                data_diction.append(yelp_search(term =res))
                data_diction[-1]['businesses'][0]['TRIP'] = top_restaurants_dic[res]
        
    if(identifier == "reviews"):
        if  not cache:
            print ("**Error: Obtain your credentials and restaurants data first and retreive reviews data.")
            exit() 
        print("Getting data from Review APIs, please wait...")
        data_diction =reviews_in_cache(cache,api_key)  
   
    return data_diction






CACHE_TRIPA = "cache_tripa.json"
CACHE_DETAIL = "cache_detail.json"
try:
    cache_tripa_file = open(CACHE_TRIPA, "r")
    cache_tripa_contents = cache_tripa_file.read()
    TRIPA_DICTION = json.loads(cache_tripa_contents)
    cache_tripa_file.close()
except:
    TRIPA_DICTION = {}



try:
    cache_tripa_file = open(CACHE_DETAIL, "r")
    cache_tripa_contents = cache_tripa_file.read()
    TRIPA_DETAIL = json.loads(cache_tripa_contents)
    cache_tripa_file.close()
except:
    TRIPA_DETAIL= {}



headers = {
        'User-Agent': 'UMSI  Project - Python Web Scraping',
        'From': 'youremail@domain.com',
        'Course-Info': 'https://www.si.umich.edu/programs/courses/507'
    }
def get_unique_key(url):
    return url

def make_request_using_cache_crawl(url,dictaionary,cache):
    unique_ident = get_unique_key(url)

    if unique_ident in dictaionary:
        return dictaionary[unique_ident]
    else:
        resp = requests.get(url,headers = headers)
        dictaionary[unique_ident] = resp.text 
        dumped_json_cache_crawl = json.dumps(dictaionary, indent=4)
        fw = open(cache,"w")
        fw.write(dumped_json_cache_crawl)
        fw.close() 
        return dictaionary[unique_ident]

def make_request_using_cache_crawl_rating(url,dictaionary,cache):
    unique_ident = get_unique_key(url)

    if unique_ident in dictaionary:
        return dictaionary[unique_ident]
    else:
        resp = requests.get(url,headers = headers)
        details_page_soup = BeautifulSoup(resp.text, "html.parser")
        rating = details_page_soup.find('span',class_="restaurants-detail-overview-cards-RatingsOverviewCard__overallRating--nohTl").next_element


        dictaionary[unique_ident] = rating
        dumped_json_cache_crawl = json.dumps(dictaionary, indent=4)
        fw = open(cache,"w")
        fw.write(dumped_json_cache_crawl)
        fw.close() 
        return dictaionary[unique_ident]


  


def get_info_tripa(page=""):
    #print(page)
    baseurl = "https://www.tripadvisor.com/Restaurants-g42139-"+ page+"-Detroit_Michigan.html#EATERY_LIST_CONTENTS"
    print('Get the restaurant for the TripAdvisor')
    page_text = make_request_using_cache_crawl(baseurl,TRIPA_DICTION,CACHE_TRIPA)
    page_soup = BeautifulSoup(page_text, "html.parser")
    results_list = page_soup.find_all('div',class_ = "_1llCuDZj")
    rating_dic = {}

    for i in results_list:
        try:
            if  i.find('div',class_="_1j22fice") == None:
                p = i.find('a',class_ = "_15_ydu6b").next_element.next_element.next_element.next_element.next_element
                s = i.find('a',class_ = "_15_ydu6b").next_element
                detail_url = 'https://www.tripadvisor.com' + i.find('a',class_ = "_15_ydu6b")["href"]
                details_page_rating = make_request_using_cache_crawl_rating(detail_url,TRIPA_DETAIL,CACHE_DETAIL)
                rating_dic[p] = details_page_rating
        except:
            continue
    return rating_dic

x = get_info_tripa()
y = get_info_tripa("oa30")
z = get_info_tripa("oa60")
h = get_info_tripa("oa90")
top_restaurants = list(x.keys()) + list(y.keys()) + list(z.keys()) + list(h.keys())
top_restaurants_dic = {**x, **y, **z, **h} 

print(top_restaurants)








    






    
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
        csv_writer.writerow(["restaurant_id", "restaurant_name", "categories", "price_level","trip_ratings","ratings", "review_counts", "state", "city", "street_address", "latitude", "longitude"])
        
        for restaurant in restaurants_list:
            csv_writer.writerow([restaurant.id, restaurant.name, restaurant.categories, restaurant.price, restaurant.trip_ratings,restaurant.ratings, restaurant.review_counts, restaurant.state, restaurant.city, 
            restaurant.street_address, restaurant.latitude, restaurant.longitude])
            
    print ("Writing restaurants'information on {}...".format(filename))


def write_restaurants_file_30(restaurants_list, filename):
    """Write the restaurants' informatino on csv file #30

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
        csv_writer.writerow(["restaurant_id", "restaurant_name", "categories", "price_level","trip_ratings","ratings", "review_counts", "state", "city", "street_address", "latitude", "longitude"])
        count = 0
        for restaurant in restaurants_list:
            if count == 50:
                break
            csv_writer.writerow([restaurant.id, restaurant.name, restaurant.categories, restaurant.price, restaurant.trip_ratings,restaurant.ratings, restaurant.review_counts, restaurant.state, restaurant.city, 
            restaurant.street_address, restaurant.latitude, restaurant.longitude])
            count += 1
            
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
        self.trip_ratings = rest_obj["TRIP"]
        self.ratings = rest_obj["rating"]
        self.review_counts = rest_obj["review_count"]
        self.state = rest_obj["location"]["state"]
        self.city = rest_obj["location"]["city"]
        self.street_address = rest_obj["location"]["address1"]
        self.latitude = rest_obj["coordinates"]["latitude"]
        self.longitude = rest_obj["coordinates"]["longitude"]
        
    
    def __repr__(self):
        return "<A Restaurant Object: 'name':{}, 'price':{},trip_ratings:{} ,ratings: {}, city: {}, address:{}>".format(self.name, self.price, self.trip_ratings,self.ratings, self.city, self.street_address)
        
    
    def __contains__(self, name):
        return name in self.name
               





# Set up for cache file name

CACHE_FNAME = "cache_contents.json" # a cache file to save the returned data on restaurants
REVIEWS_FNAME = "reviews.json" # a cache file to save the reviews on Ann Arbor's restaurants

CACHE_DICTION = open_cache(CACHE_FNAME)
REVIEWS_DICTION = open_cache(REVIEWS_FNAME)


# Get restaurants data and reviews data
CACHE_DICTION = get_data(CACHE_FNAME, identifier = "restaurants") # a python dictionary to store  restaurants data
REVIEWS_DICTION = get_data(REVIEWS_FNAME, identifier = "reviews", cache = CACHE_DICTION) # a python dictionary to store reviews data 
# Create restaurant object for each restaurant retrieved in CACHE_DICTION, and save all in a list
detroit_restaurants = []
businesses = []
for c in CACHE_DICTION:
    
    businesses.append(c["businesses"])

for business in businesses:
    if business != []:
        rest_obj = Restaurant(business[0])
        detroit_restaurants.append(rest_obj)


# Write each restaurant's information on restaurants.csv file
REST_CSV_FNAME = "restaurants.csv"
write_restaurants_file(restaurants_list = detroit_restaurants, filename = REST_CSV_FNAME)
write_restaurants_file_30(restaurants_list = detroit_restaurants, filename = 'restaurant_30.csv')
# Write each restaurant's reviews on reviews.csv file
REV_CSV_FNAME = "reviews.csv"
write_reviews_file(reviews_dict = REVIEWS_DICTION, filename = REV_CSV_FNAME)



# ---------------------------------------------------------------------
# Database Helper Function
# ---------------------------------------------------------------------

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
    rest_dict["trip_ratings"] = rest_obj.trip_ratings
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

# ---------------------------------------------------------------------
# Construct Database 
# ---------------------------------------------------------------------

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
                "review_1" TEXT NOT NULL , 
                "review_2" TEXT NOT NULL , 
                "review_3" TEXT NOT NULL 
            );
        '''
    try:
        cur.execute(statement)
    except:
        print("Fail to create table.")
    conn.commit()


    statement = '''
            CREATE TABLE "Restaurants" (
                'Id' INTEGER PRIMARY KEY AUTOINCREMENT, 
                "restaurant_name" TEXT NOT NULL,
                "categories" TEXT NOT NULL,
                "price_level_id" INTEGER , 
                "trip_ratings" REAL NOT NULL, 
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


init_tables()
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
conn.commit()


for restaurant in detroit_restaurants:
    review_dict = get_reviews_dict(REVIEWS_DICTION[restaurant.id])
    try:
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
    except:
        print("Fail to connect to the initial database.")
    #print(len(list(review_dict.keys())))
    insertion = (None,review_dict["review_1"],review_dict["review_2"],review_dict["review_3"])
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
    review_id = int(res[0][0])
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
   
    insertion = (None,rest_dict["restaurant_name"],rest_dict["categories"],rest_dict["price_level_id"],rest_dict["trip_ratings"],rest_dict["ratings"],rest_dict["review_count"],rest_dict["longitude"],rest_dict["latitude"],rest_dict["review_id"])
    statement = '''
    INSERT INTO Restaurants
    VALUES (?,?,?,?,?,?,?,?,?,?)
    '''
    cur.execute(statement,insertion)
    conn.commit()





def get_top50_form():
    # global res_list
    try:
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
    except:
        print("Fail to connect to the initial database.")



    statement = '''
            SELECT r.restaurant_name, r.categories, p.price_level, r.trip_ratings, r.ratings, r.review_count FROM Restaurants r
            JOIN PriceLevel p ON p.Id = r.price_level_id
            ORDER BY r.trip_ratings DESC LIMIT 50
            );
        '''


    cur.execute(statement)
    results = cur.fetchall()
    res_list = []
    for i in results:
        res_list.append([i[0],i[1],'{}, {}, {}{}'.format(i[2],i[3],i[4],i[5]),i[6],i[7],int(i[8]),int(i[9])])

print('----------------')
print('Process Completed!')



def get_top50_list():
    try:
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
    except:
        print("Fail to connect to the initial database.")



    statement = '''
            SELECT r.restaurant_name, r.categories, p.price_level, r.trip_ratings, r.ratings, r.review_count FROM Restaurants r
            JOIN PriceLevel p ON p.Id = r.price_level_id
            ORDER BY r.trip_ratings DESC LIMIT 50 
        '''
    cur.execute(statement)
    results = cur.fetchall()
    #print(results)
    name_lt = []
    categories_lt = []
    price_level_lt = []
    ratings_lt = []
    review_count_lt = []
    number_list = list(range(1,51))
    for i in results:
        name_lt.append(i[0])
        categories_lt.append(i[1])
        price_level_lt.append(i[2])
        ratings_lt.append('{},{}'.format(i[3],i[4]))
        review_count_lt.append(i[5])

    trace = go.Table(
        header = dict(values=['#','Restaurant Name','Categories','Price','Ratings from 2 website','Review Count']),
        cells = dict(values=[number_list,name_lt,categories_lt,price_level_lt,ratings_lt,review_count_lt]))
    data = [trace] 
    div = plot(data,filename = 'basic_table',output_type = 'div')
    conn.commit()
    conn.close()
    return div


def price_bar_plot():
    try:
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
    except:
        print("Fail to connect to the initial database.")

    statement = '''
            SELECT DISTINCT r.restaurant_name, p.price_level FROM Restaurants r
            JOIN PriceLevel p ON p.Id = r.price_level_id
            ORDER BY r.trip_ratings DESC LIMIT 50 
        '''
    cur.execute(statement)
    results = cur.fetchall()
    x = []
    y = []
     
    for i in results:
        x.append(i[0])
        y.append(i[1])

    conn.commit()
    conn.close()
    
    z = []
    for i in y:
        if i == '$':
            z.append(1)
        elif i == '$$':
            z.append(2)
        elif i == '$$$':
            z.append(3)
        else:
            z.append(4)
        
   
    bar_data = [go.Bar( name='SF Zoo',x=x, y=z,text=z,
            textposition='auto')]
   
    div = plot(bar_data, filename='price_bar_chart', output_type='div')
    return div
    

def price_pie_plot():
    try:
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
    except:
        print("Fail to connect to the initial database.")
    statement = '''
            SELECT p.price_level, COUNT(*)  FROM PriceLevel p 
            JOIN Restaurants r ON p.Id = r.price_level_id
			GROUP BY p.price_level
            ORDER BY COUNT(*) DESC LIMIT 50 
        '''
    cur.execute(statement)
    
    
    result = cur.fetchall()
    labels = []
    values = []
    for i in result:
        labels.append(i[0])
        values.append(i[1])

    conn.commit()
    conn.close()

    trace = go.Pie(labels=labels, values=values)

    div = plot([trace], filename='price_pie_chart', output_type='div')
    return div

def get_top50_form():
    # global res_list
    try:
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
    except:
        print("Fail to connect to the initial database.")

    

    statement = '''
            SELECT r.restaurant_name, r.categories, p.price_level, r.trip_ratings, r.ratings, r.review_count FROM Restaurants r
            JOIN PriceLevel p ON p.Id = r.price_level_id
            ORDER BY  r.trip_ratings LIMIT 50 
        '''
    

    cur.execute(statement)
    results = cur.fetchall()
    
    res_list = []
    for i in results:
        res_list.append([i[0],i[1],i[2],int(i[3]),int(i[4]),int(i[5])])
    conn.commit()
    conn.close()

    return res_list



def get_restaurants_sorted(sortby='ratings', sortorder='desc'):
    if sortby == 'yelp_ratings':
        sortcol = 4
    elif sortby == 'reviews':
        sortcol = 5
    elif sortby == 'trip_ratings':
        sortcol = 3
    
    else:
        sortcol = 3
    rev = (sortorder == 'desc')
    results = get_top50_form()
    sorted_list = sorted(results, key=lambda row: row[sortcol], reverse=rev)
    return sorted_list


def get_review_list():
    try:
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
    except:
        print("Fail to connect to the initial database.")


    statement = '''
            SELECT r.restaurant_name,r.trip_ratings,e.review_1,e.review_2,e.review_3
            FROM Reviews e 
            JOIN Restaurants r ON e.Id = r.review_id
            ORDER BY  r.trip_ratings LIMIT 50 
        '''
    cur.execute(statement)
    results = cur.fetchall()
    name_lt = []
    r1 = []
    r2 = []
    r3 = []
    number_list = list(range(1,51))
    for i in results:
        name_lt.append(i[0])
        r1.append(i[2])
        r2.append(i[3])
        r3.append(i[4])
    
    trace = go.Table(
        header = dict(values=['#','Restaurant Name','Review_1','Review_2','Review_3']),
        cells = dict(values=[number_list,name_lt,r1,r2,r3]))


    data = [trace] 
    div = plot(data,filename = 'basic_table',output_type = 'div')
    conn.commit()
    conn.close()
    return div



def plot_rating_line():
    try:
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
    except:
        print("Fail to connect to the initial database.")

    statement = '''
            SELECT  r.trip_ratings, COUNT(*) FROM Restaurants r
            GROUP BY r.trip_ratings
            ORDER BY trip_ratings DESC 
    '''


   
    cur.execute(statement)
    resultT = cur.fetchall()
    #tname = []
    trating = []
    trating_count = []
    for i in resultT:
        trating.append(i[0])
        trating_count.append(i[1])

    statement = '''
            SELECT  r.ratings, COUNT(*) FROM Restaurants r
            GROUP BY r.ratings
            ORDER BY ratings DESC 
    '''
    cur.execute(statement)
    resulty = cur.fetchall()
    
    yrating = []
    yrating_count = []
    for i in resulty:
        yrating.append(i[0])
        yrating_count.append(i[1])

    conn.commit()
    conn.close()    

    trace0 = go.Scatter(
        x = trating,
        y = trating_count,
        mode = 'lines+markers',
        name = 'TripAdvisor Ratings Distribution'
        )

    trace1 = go.Scatter(
        x = yrating,
        y = yrating_count,
        mode = 'lines+markers',
        name = 'Yelp Ratings Distribution'
        )
    data = [trace0,trace1]
    div = plot(data, filename='rating line chart', output_type='div')
    return div











    

   
        

   

    

















