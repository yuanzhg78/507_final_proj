# SI507 Final Project-YUAN ZHANG
The goal of the project is to get data from TripAdvisor and Yelp API in Detroit's restaurant information by using Python language including Web API, websit scraping and crawling，Flask, Plotly, SQL database usage and so on. The original data are from TripAdvisor webpage and YELP Fsion API (search API and reviews API). And the data are stored in the database for query and data visualization.
And there is a Flask that is used to construct the interaction with users. In this app, users have 6 options, the details will be shown below.

## Data Source:
2.1 TripAdvisor is an America-based website providing hotel and restaurant reviews. This project only focuses on the restaurants in Detroit. Multiple level web pages have been scraped and crawled (including restaurant list page and each restaurant's details page) by using BeautifulSoup. The information of the top 120 restaurants and each restaurant’s ratings have been cached in a JSON file named "cache_tripa.json" and cache_detail.json.
web_site: https://www.tripadvisor.com/Restaurants-g42139-"+ page+"-Detroit_Michigan.html#EATERY_LIST_CONTENTS"

2.2 Yelp is an application that provides restaurants' information/reviews. After getting the top 120 restaurant list from the TripAdvisor, I use the Yelp Fusion search API to search the restaurant name and it will return the detail information for each restaurant. The restaurants detail information and the reviews of each restaurant have been cached in a JSON file named “cache_contents.json and reviews.json. There will be 3 reviews for each restaurant.
Yelp Fusion API:
* API documentation: https://www.yelp.com/developers/documentation/v3/get_started
* Search API documentation:https://www.yelp.com/developers/documentation/v3/business_search
* Reviews API documentation:
https://www.yelp.com/developers/documentation/v3/business_reviews


### CSV files

There are two csv files that contain the information we have gained. Each csv's column names are provided below.

* restaurants.csv (saves restaurant basic information on name, category, rating, price level and location)
  * restaurant_id: the registered id of the restaurant
  * restaurant_name: the name of the restaurant
  * category: which categories the restaurant belongs to, eg. Coffee & Tea. can be multiple categories. stored in a list.
  * price_leve: range from $ to $$$$
  * trip_rating: range from 1 to 5, on a 1/2 interval from TripAdvisor
  * ratings: range from 1 to 5, on a 1/2 interval
  * review_counts: total number of reviews
  * state: the location of the restauant
  * city
  * street_address
  * latitude
  * longitude
  

* reviews.csv
   * restaurant_id: the registered id of the restaurant
   * reiview_1: one review of the customer
   * review_2: one review of the customer
   * review_3: one review of the customer


### Database

There will be three tables stored in the database:

* Table1: Restaurants
  * id: PRIMARY KEY
  * restaurant_name
  * price_level
  * trip_ratings
  * ratings
  * reviews_count
  * logitude
  * latitude
  * category id: FOREIGN KEY points to Table2 Category(id)
  * review id:  FOREIGN KEY points to Table3 Reviews(id)
  
* Table2: PriceLevel
  * id: PRIMARY KEY
  * price_level
  
* Table3: Reivews
  * id: PRIMARY KEY
  * review_1
  * review_2
  * review_3
  


## Instructions
The project is a bit completed. Here's **how to run the code**!
#### Step 1: Get an API key from Yelp API!
 [1] Go to Yelp API and apply an API key using the link below: "https://www.yelp.com/developers/v3/manage_app".<br/>
 [2] Create a "secrets.py" file and put your API key into it. The content format is like this: api_key =""<br/>

#### Step 2: pip3 install the required package for the project!
 [1] Pip install the required libraries from **requirements.txt** using <br/>
```
 pip install -r requirements.txt
```
#### Step 3: Run the main code of the project
 [1] using Python3 to run apps.py 

## Interactions
[0] Homepage: There are 6 options for the user. The detail information of each link is shown below.<br/>
[1] Link “Detroit Top50 Restaurants” is presenting the Top50 restaurants ranked by the ratings from the TripAdvisor using HTML Tables. The restaurant name, price_level, ratings from different apps, category, reviews_count are list inside. <br/>
And user can sort the data by selecting different items and the sequence of it using Flask Forms (TOP or DESC). There are 3 kinds of items: ratings from TripAdvisor (default).
[2] Link “Map of the Detroit restaurants” can show the location of the restaurants. I will use Tableau to generate the map, and it can be displayed on the web. I will use the longitude and latitude to locate the place. When user click on the restaurant point on the map, user can see the detail information of the restaurant (include ratings and the number of reviews)
The detail can be seen from restaurants_map.twb.<br/>
[3] Link “Reviews of the top restaurants” will show 3 reviews for each restaurant using HTML tables.<br/>
[4] Link “Ratings Distribution Comparison” provides the comparison of ratings between TripAdvisor and Yelp for ratings using Line Chart from Plotly.<br/>
[5] Link “Price level Status” gives the view for the price level of the restaurants using Bar Chart or Pie Chart from Plotly (show the distribution of the price level).<br/>
[6] Link “Detroit Top50 Restaurants Table” is a table view to check the information of the TOP50 restaurant in Detroit (convenient to use).









