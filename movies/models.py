from django.db import models


class Location(models.Model):
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    location = models.CharField(max_length=200, unique=True)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    
    def data(self):
        return {
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude
        }
    

class GeocodingCache(models.Model):
    location = models.OneToOneField(Location)
    date_modified = models.DateTimeField(auto_now=True)
    data = models.TextField()


class People(models.Model):
    name = models.CharField(max_length=200, unique=True)  # assume people have unique names, since there is no people_id in the data


class Company(models.Model):
    name = models.CharField(max_length=200, unique=True)  # assume companies have unique names


# movies shot in san francisco
class Movie(models.Model):
    title = models.CharField(max_length=200, unique=True)  # assume movies have unique names, in a bigger dataset this might not be the case
    year = models.PositiveSmallIntegerField()
    production_company = models.ForeignKey(Company, related_name='movies_produced')
    distributor = models.ForeignKey(Company, related_name='movies_distributed', null=True)
    director = models.ForeignKey(People, related_name='movies_directed')
    writer = models.ForeignKey(People, related_name='movies_written', null=True)
    
    def data(self):
        return {
            'title': self.title,
            'year': self.year,
            'production_company': None if not self.production_company else self.production_company.name,
            'distributor': None if not self.distributor else self.distributor.name,
            'director': None if not self.director else self.director.name,
            'writer': None if not self.writer else self.writer.name,
            'actors': [a.actor.name for a in sorted(self.actors.all(), key=lambda x: x.order)]
        }


class MovieActor(models.Model):
    movie = models.ForeignKey(Movie, related_name='actors')
    actor = models.ForeignKey(People)
    order = models.PositiveSmallIntegerField()  # data says Actor1 Actor2 Actor3, let's just preserve this order
    
    
class MovieLocation(models.Model):
    movie = models.ForeignKey(Movie)
    location = models.ForeignKey(Location)
    fun_facts = models.TextField(null=True)
    
    def data(self):
        loc_data = self.location.data()
        loc_data.update({'fun_facts': self.fun_facts})
        return loc_data
    
