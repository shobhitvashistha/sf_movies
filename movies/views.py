import json

from django.shortcuts import render

from movies.models import Movie, MovieLocation
from sf_movies.settings import MAPS_API_KEY
from django.http.response import HttpResponse


# Create your views here.
def index(request):
    data = {
        'center': {'lat': 37.7577, 'lng': -122.4376},
        'api_key': MAPS_API_KEY,
        'movies_list': json.dumps(list(Movie.objects.values('id', 'title')))
    }
    return render(request, 'index.html', data)


def movie_locations(request, movie_id):
    try:
        movie = Movie.objects.select_related('production_company', 'distributor', 'director',
                                             'writer').prefetch_related('actors', 'actors__actor').get(id=movie_id)
    except Movie.DoesNotExist:
        return JSONResponse({'error': 'Movie not found'}, status=404)
    
    movie_locs = MovieLocation.objects.filter(movie_id=movie).select_related('location')
    
    data = {
        'movie': movie.data(),
        'locations': [movie_loc.data() for movie_loc in movie_locs]
    }
    return JSONResponse(data)


def JSONResponse(data, *args, **kwargs):
    return HttpResponse(json.dumps(data), content_type='application/javascript; charset=utf8', *args, **kwargs)