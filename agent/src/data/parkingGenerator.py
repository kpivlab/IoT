import csv
import random

# Filepath to the parking.csv file
filepath = '/home/vlab/Public/IoT/project_template/agent/src/data/parking.csv'

# Function to generate random latitude and longitude within a specific range
def generate_random_coordinates():
    latitude = random.uniform(50.0, 51.0)  # Example range for latitude
    longitude = random.uniform(30.0, 31.0)  # Example range for longitude
    return latitude, longitude

# Open the file in append mode
with open(filepath, 'a', newline='') as csvfile:
    writer = csv.writer(csvfile)
    
    # Generate and write 200 random sets of parking data
    for _ in range(200):
        empty_count = random.randint(0, 10)  # Random empty count between 0 and 10
        latitude, longitude = generate_random_coordinates()
        writer.writerow([empty_count, latitude, longitude])

print("200 random sets of parking data have been added to parking.csv")