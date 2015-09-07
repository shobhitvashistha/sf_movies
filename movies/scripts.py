import csv
import json
import os
import time
from urllib import quote_plus
import urllib2

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from movies.models import People, Company, Location, Movie, MovieActor, \
    MovieLocation, GeocodingCache
from sf_movies.settings import BASE_DIR, MAPS_API_KEY


exclude_names = {'', 'N/A'}
excluded_id = {'': None, 'N/A': None}

google_geocoding_url = 'https://maps.googleapis.com/maps/api/geocode/json'
geocoding_link = google_geocoding_url + '?address={address}&components=administrative_area:San+Francisco|country:US&key=' + MAPS_API_KEY

google_api_wait = (1.0 / 5.0)  # google free api limit: 5 queries per second


def flatten(nested_list):
    return (item for sublist in nested_list for item in sublist)


def get_from_cache_or_google(loc):
    # if data is stored in cache, no need to hit google api
    try:
        data = GeocodingCache.objects.get(location=loc.id).data
        json_data = json.loads(data)
        return json_data
    except GeocodingCache.DoesNotExist:
        pass
    
    # not in cache, so we must ask google
    addr = quote_plus(loc.location.encode('utf-8'))
    link = geocoding_link.format(address=addr)
    
    # wait if not enough time has passed since last api call
    last_api_call = GeocodingCache.objects.aggregate(max=Max('date_modified'))['max']
    wait = (-1.0) if not last_api_call else (google_api_wait - (timezone.now() - last_api_call).total_seconds())
    if wait > 0.0:
        time.sleep(wait)
    
    # make the api call
    data = urllib2.urlopen(link).read()
    json_data = json.loads(data)
    print link
    
    # now that we know that data is in json format, store it in cache
    GeocodingCache.objects.create(location_id=loc.id, data=data)
    
    return json_data


def store_lat_lon():
    locations = Location.objects.filter(latitude=None).all()
    
    for loc in locations:
        loc_data = get_from_cache_or_google(loc)
        try:
            lat_lon = loc_data['results'][0]['geometry']['location']
            lat = lat_lon['lat']
            lon = lat_lon['lng']
            Location.objects.filter(id=loc.id).update(latitude=lat, longitude=lon)
        except IndexError:
            print 'No Results:', loc.location


def load_data():
    """
    Load the data in csv file to the database, using python
    
    If the dataset is large this approach would be very slow, it'll be better to create
    a temp table and load all the data at once (using mysql load data infile). Then we can
    normalize the data into different tables
    """ 
    csv_path = os.path.join(BASE_DIR, 'data', 'Film_Locations_in_San_Francisco.csv')
    with open(csv_path, 'rb') as data_file:
        reader = csv.reader(data_file)
        list_data = list(reader)
        # converting into a dict to make things more clear, there's no real need for this step
        # it just makes the code easy to read and understand
        data = [{
                    'title': row[0].strip(), 'year': int(row[1].strip()), 'location': row[2].strip(), 'fun_facts': row[3].strip(),
                    'production_company': row[4].strip(), 'distributor': row[5].strip(), 'director': row[6].strip(),
                    'writer': row[7].strip(), 'actor1': row[8].strip(), 'actor2': row[9].strip(), 'actor3': row[10].strip()
                } for row in list_data[1:]]
        
        # all of the data except for locations and fun facts is common for movie
        uniq_movie_data = {}
        for row in data:
            if row['title'] not in uniq_movie_data:
                uniq_movie_data[row['title']] = {k: row[k] for k in ['title', 'year', 'production_company', 'distributor',
                                                                        'director', 'writer', 'actor1', 'actor2', 'actor3']}
        
        uniq_locations = set(row['location'] for row in data).difference(exclude_names)
        uniq_companies = set(flatten([row['production_company'], row['distributor']] for row in uniq_movie_data.values())).difference(exclude_names)
        uniq_people = set(flatten([row['director'], row['writer'], row['actor1'], row['actor2'], row['actor3']]
                             for row in uniq_movie_data.values())).difference(exclude_names)
                             
        # manually assign ids, we are populating the database from scratch, so this shouldn't be an issue
        locations = [(loc, i + 1) for i, loc in enumerate(uniq_locations)]
        companies = [(com, i + 1) for i, com in enumerate(uniq_companies)]
        people = [(ppl, i + 1) for i, ppl in enumerate(uniq_people)]
        movies = [(mov, i + 1) for i, mov in enumerate(uniq_movie_data.keys())]
        
        # create company, people, location id maps for fast lookup
        company_id_map = dict(companies)
        people_id_map = dict(people)
        location_id_map = dict(locations)
        
        company_id_map.update(excluded_id)
        people_id_map.update(excluded_id)
        location_id_map.update(excluded_id)
        
        movie_id_map = dict(movies)
        
        # gather instances for bulk_create
        people_to_create = [People(id=i, name=name) for name, i in people]
        companies_to_create = [Company(id=i, name=name) for name, i in companies]
        locations_to_create = [Location(id=i, location=loc, city='San Francisco', state='CA', country='USA') for loc, i in locations]
        
        movies_to_create = [Movie(id=movie_id_map[row['title']], title=row['title'], year=row['year'],
                            production_company_id=company_id_map[row['production_company']],
                            distributor_id=company_id_map[row['distributor']], director_id=people_id_map[row['director']],
                            writer_id=people_id_map[row['writer']]) for row in uniq_movie_data.values()]
        
        movie_actors_to_create = []
        for row in uniq_movie_data.values():
            actors = [row[k] for k in ['actor1', 'actor2', 'actor3']]
            actors = [a for a in actors if a]
            movie_id = movie_id_map[row['title']]
            movie_actors_to_create.extend(MovieActor(movie_id=movie_id, actor_id=people_id_map[a],
                                                     order=(i + 1)) for i, a in enumerate(actors))
        
        movie_locations_to_create = [MovieLocation(movie_id=movie_id_map[row['title']], location_id=location_id_map[row['location']],
                                                   fun_facts=(row['fun_facts'] or None)) for row in data if row['location']]
        
        # all db hits inside one transaction
        with transaction.atomic():
            # bulk create people
            People.objects.bulk_create(people_to_create)
            # bulk create companies
            Company.objects.bulk_create(companies_to_create)
            # bluk create locations
            Location.objects.bulk_create(locations_to_create)
            
            # bulk create movies
            Movie.objects.bulk_create(movies_to_create)
            # bulk create movie actors
            MovieActor.objects.bulk_create(movie_actors_to_create)
            # bulk create locations
            MovieLocation.objects.bulk_create(movie_locations_to_create)
            
    