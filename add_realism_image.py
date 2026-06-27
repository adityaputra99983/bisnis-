import os
import django
import urllib.request
from django.core.files.base import ContentFile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bisnis.settings')
django.setup()

from tattoo.models import Service

# Download image
url = "https://images.unsplash.com/photo-1598371839696-5c5bb00bdc28?q=80&w=800"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    response = urllib.request.urlopen(req)
    image_content = response.read()

    # Get the service
    service = Service.objects.filter(name__icontains="Realism").first()
    if service:
        service.image.save('realism_tattoo.jpg', ContentFile(image_content), save=True)
        print("Successfully added image to", service.name)
    else:
        print("Service 'Realism' not found.")
except Exception as e:
    print("Error:", e)
