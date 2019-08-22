
# coding: utf-8

# Based on TWD tutorial:
# https://towardsdatascience.com/web-scraping-craigslist-a-complete-tutorial-c41cea4f4981?gi=78313d2324de

# In[1]:


str_query = 'https://vancouver.craigslist.org/search/apa?query=champlain+heights&availabilityMode=0'


# In[2]:


from requests import get
from bs4 import BeautifulSoup
from time import sleep
import re
from random import randint #avoid throttling by not sending too many requests one after the other
from warnings import warn
from time import time
from IPython.core.display import clear_output
import numpy as np
import math
import pandas as pd
from datetime import datetime
import matplotlib.pylab as pylab
import matplotlib.pyplot as plt
import seaborn as sns
import datetime
import pygsheets

#get the first page of the east bay housing prices
response = get(str_query)
html_soup = BeautifulSoup(response.text, 'html.parser')

#get the macro-container for the housing posts
posts = html_soup.find_all('li', class_= 'result-row')
#print(type(posts), len(posts)) #check that I got a ResultSet & 120 records

#find the total number of posts to find the limit of the pagination
results_num = html_soup.find('div', class_= 'search-legend')
results_total = int(results_num.find('span', class_='totalcount').text) #pulled the total count of posts as the upper bound of the pages array

print(html_soup.title.string)
print(results_total, "Records on", math.ceil(results_total/120), "page(s)")


# In[3]:


#build out the loop

#each page has 119 posts so each new page is defined as follows: s=120, s=240, s=360, and so on. So we need to step in size 120 in the np.arange function
pages = np.arange(0, results_total+1, 120)

iterations = 0

post_timing = []
post_hoods = []
post_title_texts = []
bedroom_counts = []
sqfts = []
post_links = []
post_prices = []

collection_latitude = []
collection_longitude = []
collection_accuracy = []
collection_attribute = []
post_body = []

for page in pages:
    
    #get request
    response = get(str_query            
                   + "s=" #the parameter for defining the page number 
                   + str(page) #the page number in the pages array from earlier
                  )

    sleep(randint(1,5))
     
    #throw warning for status codes that are not 200
    if response.status_code != 200:
        warn('Request: {}; Status code: {}'.format(requests, response.status_code))
        
    #define the html text
    page_html = BeautifulSoup(response.text, 'html.parser')
    
    #define the posts
    posts = html_soup.find_all('li', class_= 'result-row')
        
    #extract data item-wise
    for post in posts:

        if post.find('span', class_ = 'result-hood') is not None:

            #posting date
            #grab the datetime element 0 for date and 1 for time
            post_datetime = post.find('time', class_= 'result-date')['datetime']
            post_timing.append(post_datetime)

            #neighborhoods
            post_hood = post.find('span', class_= 'result-hood').text
            post_hoods.append(post_hood)

            #title text
            post_title = post.find('a', class_='result-title hdrlnk')
            post_title_text = post_title.text
            post_title_texts.append(post_title_text)

            #post link
            post_link = post_title['href']
            post_links.append(post_link)
            
            #parse post at the above link
            post_link_response = get(post_link)
            soup = BeautifulSoup(post_link_response.text, 'html.parser')   
            
            if soup.find('section', id = 'postingbody') is not None:
                    post_body.append(soup.find('section', id = 'postingbody').text.strip())
            else:
                    post_body.append(np.nan)

            if soup.find('div', id = 'map') is not None:
                    #latitude
                    post_latitude =  soup.find('div', id = 'map')['data-latitude']
                    collection_latitude.append(post_latitude)
                    #longitude
                    post_longitude =  soup.find('div', id = 'map')['data-longitude']
                    collection_longitude.append(post_longitude)
                    #accuracy
                    post_accuracy =  soup.find('div', id = 'map')['data-accuracy']
                    collection_accuracy.append(post_accuracy)
            else:
                    collection_latitude.append(np.nan)
                    collection_longitude.append(np.nan)
                    collection_accuracy.append(np.nan)
                 
            # other attributes
            attr_groups = soup.find_all('p', class_ = 'attrgroup')
            post_attributes = []
            for attr_group in attr_groups:
                    #print(attr_group.text.strip())
                    post_attributes.append(attr_group.text.strip().replace("\n", "|"))
            collection_attribute.append(post_attributes) 
                    
            #removes the \n whitespace from each side, removes the currency symbol, and turns it into an int
            #print(post_link, re.findall(r"\$\d+(?:\.\d+)?", post.text)[0].replace("$", ""))
            post_price = int(re.findall(r"\$\d+(?:\.\d+)?", post.text)[0].replace("$", "")) 
            post_prices.append(post_price)
            
            if post.find('span', class_ = 'housing') is not None:
                
                #if the first element is accidentally square footage
                if 'ft2' in post.find('span', class_ = 'housing').text.split()[0]:
                    
                    #make bedroom nan
                    bedroom_count = np.nan
                    bedroom_counts.append(bedroom_count)
                    
                    #make sqft the first element
                    sqft = int(post.find('span', class_ = 'housing').text.split()[0][:-3])
                    sqfts.append(sqft)
                    
                #if the length of the housing details element is more than 2
                elif len(post.find('span', class_ = 'housing').text.split()) > 2:
                    
                    #therefore element 0 will be bedroom count
                    bedroom_count = post.find('span', class_ = 'housing').text.replace("br", "").split()[0]
                    bedroom_counts.append(bedroom_count)
                    
                    #and sqft will be number 3, so set these here and append
                    sqft = int(post.find('span', class_ = 'housing').text.split()[2][:-3])
                    sqfts.append(sqft)
                    
                #if there is num bedrooms but no sqft
                elif len(post.find('span', class_ = 'housing').text.split()) == 2:
                    
                    #therefore element 0 will be bedroom count
                    bedroom_count = post.find('span', class_ = 'housing').text.replace("br", "").split()[0]
                    bedroom_counts.append(bedroom_count)
                    
                    #and sqft will be number 3, so set these here and append
                    sqft = np.nan
                    sqfts.append(sqft)                    
                
                else:
                    bedroom_count = np.nan
                    bedroom_counts.append(bedroom_count)
                
                    sqft = np.nan
                    sqfts.append(sqft)
                
            #if none of those conditions catch, make bedroom nan, this won't be needed    
            else:
                bedroom_count = np.nan
                bedroom_counts.append(bedroom_count)
                
                sqft = np.nan
                sqfts.append(sqft)
                
    iterations += 1
    print("Page " + str(iterations) + " scraped successfully.\n")
    
print("Scrape complete! Number of records:", len(post_links))


# In[4]:


# convert to dataframe
scraped_data = pd.DataFrame({'posted': post_timing,
                       'neighborhood': post_hoods,
                       'post title': post_title_texts,
                       'number bedrooms (from title)': bedroom_counts,
                        'sqft': sqfts,
                        'URL': post_links,
                       'price': post_prices,
                       'body': post_body,
                       'latitude': collection_latitude,
                       'longitude': collection_longitude,
                       'accuracy': collection_accuracy,
                       'attributes': collection_attribute})

#drop duplicate URLs
scraped_data = scraped_data.drop_duplicates(subset='URL')

#make the number bedrooms to a float
scraped_data['number bedrooms'] = scraped_data['number bedrooms (from title)'].apply(lambda x: float(x))

#convert datetime string into datetime object
scraped_data['posted'] = pd.to_datetime(scraped_data['posted'])

#add identifier (query)
scraped_data['query'] = str_query

#add current timestamp
scraped_data['as_of'] = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')


# ##couple visualizations and linear regression for a for a quick analysis
# 
# params = {'legend.fontsize': 'x-large',
#           'figure.figsize': (15, 5),
#          'axes.labelsize': 'x-large',
#          'axes.titlesize':'x-large',
#          'xtick.labelsize':'x-large',
#          'ytick.labelsize':'x-large'}
# 
# pylab.rcParams.update(params)
# plt.figure(figsize=(12, 8))
# 
# sns.scatterplot(x='price', y='sqft', hue='number bedrooms', palette='summer', x_jitter=True, y_jitter=True, s=125, data=scraped_data.dropna())
# plt.legend(fontsize=12)
# plt.xlabel("Price", fontsize=18)
# plt.ylabel("Square Footage", fontsize=18);
# plt.title("Price vs. Square Footage Colored by Number of Bedrooms", fontsize=18);
# plt.show()
# 
# sns.boxplot(x='number bedrooms', y='price', data=scraped_data)
# plt.xlabel("# of bedrooms");
# plt.xticks(rotation=75)
# plt.ylabel("Price");
# plt.title("Prices by # of Bedrooms");
# plt.show()
# 
# plt.figure(figsize=(12, 8))
# sns.regplot(x='price', y='sqft', data=scraped_data.dropna());
# plt.title('Price vs. Square Footage Regression Plot');
# plt.xlabel("Price");
# plt.ylabel("Square Feet");
# plt.show()

# In[5]:


### features extraction

# housing type
def tag_housing_type(x):
    x = ''.join(x)
    if x.find("apartment") != -1:
        result = "apartment"
    elif x.find("condo") != -1:
        result = "condo"
    elif x.find("cottage/cabin") != -1:
        result = "cottage/cabin"
    elif x.find("duplex") != -1:
        result = "duplex"
    elif x.find("flat") != -1:
        result = "flat"
    elif x.find("townhouse") != -1:
        result = "townhouse"
    elif x.find("house") != -1:
        result = "house"
    elif x.find("in-law") != -1:
        result = "in-law"
    elif x.find("loft") != -1:
        result = "loft"
    elif x.find("manufactured") != -1:
        result = "manufactured"
    elif x.find("assisted living") != -1:
        result = "assisted living"
    elif x.find("land") != -1:
        result = "land"  
    else:
        result = "NA"     
    return result

# laundry
def tag_laundry(x):
    x = ''.join(x)
    if x.find("w/d in unit") != -1:  
        result = "w/d in unit"
    elif x.find("w/d hookups") != -1:  
        result = "w/d hookups"
    elif x.find("laundry in bldg") != -1:  
        result = "laundry in bldg"
    elif x.find("laundry on site") != -1:  
        result = "laundry on site"
    elif x.find("no laundry on site") != -1:  
        result = "no laundry on site"
    else:
        result = "NA"     
    return result

# parking
def tag_parking(x):
    x = ''.join(x)
    if x.find("carport") != -1:  
        result = "carport"
    elif x.find("attached garage") != -1:  
        result = "attached garage"
    elif x.find("detached garage") != -1:  
        result = "detached garage"
    elif x.find("off-street parking") != -1:  
        result = "off-street parking"
    elif x.find("street parking") != -1:  
        result = "street parking"
    elif x.find("valet parking") != -1:  
        result = "valet parking"
    elif x.find("no parking") != -1:  
        result = "no parking"
    else:
        result = "NA"     
    return result
# cats ok
def tag_cats_ok(x):
    x = ''.join(x)
    if x.find("cats are OK") != -1:  
        result = "cats ok"
    else:
        result = "NA"     
    return result
# dogs ok
def tag_dogs_ok(x):
    x = ''.join(x)
    if x.find("dogs are OK") != -1:  
        result = "dogs ok"
    else:
        result = "NA"     
    return result
# furnished
def tag_furnished(x):
    x = ''.join(x)
    if x.find("furnished") != -1:  
        result = "furnished"
    else:
        result = "NA"     
    return result
# bedrooms
def tag_bedrooms(x):
    x = ''.join(x)
    if x.find("BR") != -1:  
        result = x[:x.find("BR")]
    else:
        result = "NA"     
    return result
# bathrooms
def tag_bathrooms(x):
    x = ''.join(x)
    if x.find("Ba") != -1:  
        result = x[x.find("/ ")+1:x.find("Ba")]
    else:
        result = "NA"     
    return result

# process attributes
scraped_data['housing_type'] = scraped_data['attributes'].apply(lambda x: tag_housing_type(x))
scraped_data['laundry'] = scraped_data['attributes'].apply(lambda x: tag_laundry(x))
scraped_data['parking'] = scraped_data['attributes'].apply(lambda x: tag_parking(x))
scraped_data['cats ok'] = scraped_data['attributes'].apply(lambda x: tag_cats_ok(x))
scraped_data['dogs ok'] = scraped_data['attributes'].apply(lambda x: tag_dogs_ok(x))
scraped_data['furnished'] = scraped_data['attributes'].apply(lambda x: tag_furnished(x))
scraped_data['bedrooms'] = scraped_data['attributes'].apply(lambda x: tag_bedrooms(x))
scraped_data['bathrooms'] = scraped_data['attributes'].apply(lambda x: tag_bathrooms(x))

#scraped_data[['attributes', 'housing_type', 'laundry', 'parking', 'cats ok', 'dogs ok', 'furnished','bedrooms', 'bathrooms']].head(5)


# In[69]:


gc = pygsheets.authorize(service_file='C:/Users/svyat/Google Drive/craigslist-rent-scrape/rent-market-data-to-g-drive-d93513d8f1e5.json')
sh = gc.open_by_url('https://docs.google.com/spreadsheets/d/1bhQFfEJHaWTfKd9o6cfq0AQ3FO0a-YnvG2DfV7NNAnw')

existing = sh[0].get_as_df()
updated = existing.append(scraped_data)
sh[0].set_dataframe(updated, (1,1))


# In[19]:


#save clean data to XL for further visualization and analysis
#scraped_data.to_excel('data.xlsx', index = False)

