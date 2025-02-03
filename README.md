Traffic Light Management System
Overview
The Traffic Light Management System is designed to manage and simulate traffic light operations based on real-time traffic data. The system dynamically adjusts traffic light cycles by analyzing road traffic intensity near a given location. Using APIs like Google Roads, Geocoding, and Distance Matrix, it gathers and processes traffic data, while displaying the results through an interactive user interface.

Features
Traffic Intensity Detection: Using the Google Maps Roads API, it fetches nearby roads and calculates traffic intensities using the Distance Matrix API. Dynamic Traffic Light Simulation: Traffic lights are simulated based on traffic intensity data, dynamically adjusting the green, yellow, and red lights for each road. Real-time Traffic Data: The program fetches updated traffic data after each cycle to ensure the lights are always based on real-time information. Customizable Settings: You can input the latitude and longitude, range of the device, total life cycle of the traffic lights, and the maximum number of snapped road points to analyze. How It Works Input Details: The user provides the latitude, longitude, traffic box ID, range (in meters), total life cycle (in seconds), and the number of nearby road points to analyze. Fetching Data: The program sends requests to the Google Maps Roads API to find the nearest roads to the specified coordinates and fetches traffic intensity data using the Distance Matrix API. Traffic Light Simulation: Based on the traffic intensity data, the program simulates a traffic light system, where the road with the highest traffic intensity gets the green light, and the other roads get yellow or red lights. Real-time Updates: The traffic data is updated at the end of each cycle to ensure the lights adapt to changing traffic conditions.

Google Maps API Key
You will need a Google Maps API key with access to the following services:

Roads API
Distance Matrix API You can generate an API key by following the Google Maps API documentation.

Input Fields
Latitude: Latitude of the location to simulate traffic (e.g., 26.6608). Longitude: Longitude of the location to simulate traffic (e.g., 92.7755). Traffic Box ID: A unique identifier for the traffic light system (e.g., Box123). Range of Device (in meters): The area within which the nearest roads are fetched (e.g., 500 meters). Total Life Cycle (in seconds): The total duration of one cycle of traffic light changes (e.g., 120 seconds). Max Snapped Points: The number of nearby roads to fetch traffic data for (between 1 and 4). How to Use Input the desired location by entering latitude and longitude. Enter the traffic box ID, range, life cycle time, and max snapped points. Submit the form to start the simulation. The system will display traffic lights for each road based on real-time tra
