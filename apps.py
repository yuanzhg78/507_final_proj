
from flask import Flask, render_template, url_for
import requests
from secrets import *
import json
from final_proj import *
from flask import Flask, render_template, request
import plotly.graph_objs as go
app = Flask(__name__)

@app.route('/')
def home_page():
    html = '''
        <link rel="stylesheet" type="text/css" href="./static/f1.css"/>
        <h1 align='center'>Welcome to Yuan‘s site!</h1>
        <h3 align='center'><a href='/form'>Detroit Top50 Restaurants</a></h3>
        <h3 align='center'><a href='/map'>Map for Detroit Top50 Restaurants</a></h3>
        <h3 align='center'><a href='/reviews'>Reviews of Detroit Top50 Restaurants</a></h3>
        <h3 align='center'><a href='/rating_compare'>Ratings Distribution Comparison</a></h3>
        <h3 align='center'><a href='/price'>Price Range Status</a></h3>
        <h3 align='center'><a href='/detop50'>Detroit Top50 Restaurants Table</a></h3>
        <h1 align='center'>Find the best restaurant in Detroit!</h1>
    '''
    return html
@app.route('/detop50')
def AA_top50_list():
    
    html = '<div id="plot_top50"; style="background-color:#F9E79F;">'
    html += "<h2 align='center'>The List of Top50 Restaurants in Detroit</h2>"
    html += get_top50_list()
    
    html += '</div>'
    return html

@app.route('/reviews')
def review_top50_list():
    html = '<div id="reviews"; style="background-color:#F9E79F;">'
    html += "<h2 align='center'>Reviews of Top50 Restaurants in Detroit</h2>"
    html += get_review_list()
    html += '</div>'
    return html


@app.route('/map')
def map_top():
    return render_template("visualization.html")



@app.route('/form', methods=['GET', 'POST'])
def Restaurants_top():
    if request.method == 'POST':
        if'sortby' in request.form:
            sortby = request.form['sortby']
        else:
            sortby="top"
        if "sortorder" in request.form:
            sortorder = request.form['sortorder']
        else:
            sortorder="desc"
        seasons = get_restaurants_sorted(sortby, sortorder)
    else:
        seasons = get_restaurants_sorted()
        
    return render_template("seasons.html", seasons=seasons)


@app.route('/price')
def price():
    html = '<div id="plot_price"; style="background-color:#F9E79F;">'
    html += "<h2 align='center'>Bar Chart for Price Range Status for Top50 Restaurants</h2>"
    html += price_bar_plot()
    html += "<h2 align='center'>Pie Chart for Price Range Status for Top50 Restaurants</h2>"
    html += price_pie_plot()
    html += '</div>'
    return html



@app.route('/plot')
def plot():

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
    x_val = []
    y = []
     
    for i in results:
        x_val.append(i[0])
        y.append(i[1])
    
    conn.commit()
    conn.close()
    
    z_val = []
    for i in y:
        if i == '$':
            z_val.append(1)
        elif i == '$$':
            z_val.append(2)
        elif i == '$$$':
            z_val.append(3)
        else:
            z_val.append(4)
        
    
    bars_data = go.Bar(x=x_val, y=z_val,text = z_val, textposition='auto')
    fig = go.Figure(data=bars_data)
    div = fig.to_html(full_html=False)
    return render_template("plot.html", plot_div=div)



@app.route('/rating_compare')
def rating_compare():
    html = '<div id="plot_rating_line"; style="background-color:#F9E79F;">'
    html += "<h2 align='center'>Line Chart for Ratings Comparison between TripAdvisor and Yelp</h2>"
    html += plot_rating_line()
    html += '</div>'    
    return html




if __name__ == '__main__':  
    print('starting Flask app', app.name)  
    app.run(debug=True)







 






