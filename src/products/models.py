import random
import string
import os
from django.db import models
from django.db.models import Q
from django.db.models.signals import pre_save, post_save
from django.urls import reverse

from web_project.utils import unique_slug_generator

def get_filename_ext(filepath):
	base_name = os.path.basename(filepath)
	name, ext = os.path.splitext(base_name)
	return name, ext

# changing file name to a random interger and pathing it
def upload_image_path(instance, filename):
	# print(instance)
	char_available = string.ascii_letters + '1234567890'
	new_filename = ''.join(random.choice(char_available) for i in range(2,random.randint(0,20)))
	name, ext = get_filename_ext(filename)
	final_filename = '{new_filename}{ext}'.format(new_filename=new_filename, ext=ext)
	return "products/{new_filename}/{final_filename}".format(
			new_filename=new_filename, 
			final_filename=final_filename
			)

class ProductQuerySet(models.query.QuerySet):
	# This object extend the default query set
	def active(self):
		return self.filter(active=True)

	def featured(self):
		return self.filter(featured=True, active=True)

	# Main seach algorithm
	def search(self, query):
		lookups = ( Q(title__icontains=query) | 
				  	Q(description__icontains=query)|
				  	Q(tag__title__icontains=query)
				  	)
		# Q(price_icontains=query)
		# Q(tag__name__icontains=query)
		return self.filter(lookups).distinct()


class ProductManager(models.Manager):
	# filter(tiltle__icontains = 'string', <field> = boolean)
	def get_queryset(self):
		return ProductQuerySet(self.model, using=self._db)

	def all(self): #Product.objects.all()
		return self.get_queryset().active()

	def featured(self): #Product.objects.featured()
		return self.get_queryset().featured()

	def get_by_id(self, id):
		qs = self.get_queryset().filter(id=id)
		if qs.count() == 1:
			return qs.first()
		return None

	def search(self, query):
		return self.get_queryset().active().search(query)


class Product(models.Model):
	title 		= models.CharField(max_length=120, blank=False)
	slug 		= models.SlugField(blank=True, unique=True)
	description = models.TextField(blank=True, null=True)
	price 		= models.DecimalField(decimal_places=2, max_digits=10000)
	image		= models.ImageField(upload_to=upload_image_path, null=True, blank=True)
	featured 	= models.BooleanField(default=False) # null=True, default=True
	active  	= models.BooleanField(default=True) # null=True, default=True
	timestamp	= models.DateTimeField(auto_now_add=True)

	objects = ProductManager() #Externd the default manager

	def get_absolute_url(self):
		#return "/products/{slug}/".format(slug=self.slug)
		return reverse("products:detail", kwargs={"slug": self.slug})

	def __str__(self):
		return self.title

	@property
	def name(self):
		return self.title
	

def product_pre_save_receiver(sender, instance, *args, **kwagrs):
	if not instance.slug:
		instance.slug = unique_slug_generator(instance)

pre_save.connect(product_pre_save_receiver, sender=Product)