import tkinter as tk
import requests
import string
import time
import math
import threading
import webbrowser

# Google Maps API key
# spare API_KEY =   (Alternate API Key)
API_KEY = Your API Key 


def meters_to_degrees_latitude(meters):
    return meters / 111320


def meters_to_degrees_longitude(meters, latitude):
    return meters / (111320 * math.cos(math.radians(latitude)))


def get_nearest_road(latitude, longitude, api_key):
    roads_url = f'https://roads.googleapis.com/v1/nearestRoads?points={latitude},{longitude}&key={api_key}'
    response = requests.get(roads_url)
    if response.status_code == 200:
        data = response.json()
        if 'snappedPoints' in data:
            return data['snappedPoints']
        else:
            return []
    else:
        print("Error fetching data from Roads API")
        return []


def count_nearby_roads(latitude, longitude, api_key, range_m, max_snap_points=4):
    snapped_points = []
    unique_road_coords = set()

    lat_range = meters_to_degrees_latitude(range_m)
    lon_range = meters_to_degrees_longitude(range_m, latitude)

    directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]  # Move north, east, south, west
    for dx, dy in directions:
        i = 0
        while True:
            lat = latitude + i * lat_range * dx
            lon = longitude + i * lon_range * dy
            points = get_nearest_road(lat, lon, api_key)

            for point in points:
                coords = (point['location']['latitude'], point['location']['longitude'])
                if coords not in unique_road_coords:
                    snapped_points.append(point)
                    unique_road_coords.add(coords)

                if len(snapped_points) >= max_snap_points:
                    break

            if len(snapped_points) >= max_snap_points or len(points) == 0:
                break

            i += 1
            time.sleep(0.1)
            if i > 100:  # Safeguard to prevent infinite loop in case fewer roads are available
                break

    num_roads = len(snapped_points)
    return snapped_points, num_roads


def get_traffic_data(latitude, longitude, api_key, retries=3):
    for _ in range(retries):
        traffic_url = f'https://maps.googleapis.com/maps/api/distancematrix/json?origins={latitude},{longitude}&destinations={latitude + 0.001},{longitude + 0.001}&departure_time=now&traffic_model=best_guess&key={api_key}'
        response = requests.get(traffic_url)
        if response.status_code == 200:
            data = response.json()
            if 'rows' in data and 'elements' in data['rows'][0] and 'duration_in_traffic' in \
                    data['rows'][0]['elements'][0]:
                traffic_intensity = data['rows'][0]['elements'][0]['duration_in_traffic']['value']
                if traffic_intensity > 0:
                    return traffic_intensity
            else:
                print("No traffic data available for the specified location")
        time.sleep(0.1)

    print("Error fetching data from Traffic API or all attempts returned 0 traffic intensity")
    return None


def determine_traffic_intensities(snapped_points, api_key):
    intensities = []
    for point in snapped_points:
        intensity = get_traffic_data(point['location']['latitude'], point['location']['longitude'], api_key)
        intensities.append(intensity if intensity is not None else 0)
    return intensities


class TrafficLightGUI:
    def __init__(self, master):
        self.master = master
        self.canvas = tk.Canvas(master, width=70, height=150)
        self.canvas.pack()
        self.colors = ["red", "yellow", "green"]
        self.current_color_index = 0
        self.draw_traffic_light()

        # Create a label for the countdown timer
        self.timer_label = tk.Label(master, text="", font=("Helvetica", 14))
        self.timer_label.pack()

    def draw_traffic_light(self):
        box_width = 50
        box_height = 175
        box_left = (70 - box_width) / 2
        box_top = (150 - box_height) / 2
        box_right = box_left + box_width
        box_bottom = box_top + box_height

        self.canvas.create_rectangle(box_left, box_top, box_right, box_bottom, fill="black")

        light_size = 20
        light_left = (70 - light_size) / 2
        light_top = box_top + 20
        light_bottom = light_top + light_size

        self.lights = [
            self.canvas.create_oval(light_left, light_top + i * (light_size + 40), light_left + light_size,
                                    light_bottom + i * (light_size + 40), fill="black")
            for i in range(3)
        ]

    def update_light(self, color, countdown_time=None):
        for light in self.lights:
            self.canvas.itemconfig(light, fill="black")
        color_index = self.colors.index(color)
        self.canvas.itemconfig(self.lights[color_index], fill=color)

        # Update the timer label if a countdown time is provided
        if countdown_time is not None:
            self.update_timer(countdown_time)
        else:
            self.timer_label.config(text="")  # Clear the timer when no countdown is needed

    def update_timer(self, time_left):
        if time_left > 0:
            self.timer_label.config(text=f"{time_left} sec")
        else:
            self.timer_label.config(text="")


def fetch_new_traffic_data(snapped_points, api_key, result_holder):
    """Fetch traffic data asynchronously and store the result."""
    new_intensities = determine_traffic_intensities(snapped_points, api_key)
    result_holder.append(new_intensities)


def update_traffic_lights(root, road_names, snapped_points, traffic_lights, api_key, life_cycle_seconds):
    intensities = determine_traffic_intensities(snapped_points, api_key)
    sorted_indices = sorted(range(len(intensities)), key=lambda i: intensities[i], reverse=True)

    total_roads = len(road_names)
    half_cycle_time = life_cycle_seconds / 2
    secondary_cycle_time = half_cycle_time / (total_roads - 1)

    new_data_holder = []

    for index in range(len(sorted_indices)):
        current_road_index = sorted_indices[index]
        road_name = road_names[current_road_index]

        for i in range(total_roads):
            if i != current_road_index:
                traffic_lights[i].update_light("red")
        root.update()

        if index == 0:
            green_time = half_cycle_time
        else:
            green_time = secondary_cycle_time

        print(f"Road {road_name} green for {green_time} seconds.")
        for t in range(int(green_time), 0, -1):
            traffic_lights[current_road_index].update_light("green", countdown_time=t)
            root.update()
            time.sleep(1)

        print(f"Road {road_name} yellow for 5 seconds.")

        if index == len(sorted_indices) - 1:
            print("Fetching new traffic data during yellow light of the last road.")
            # Start fetching new traffic data in a separate thread
            traffic_thread = threading.Thread(target=fetch_new_traffic_data,
                                              args=(snapped_points, api_key, new_data_holder))
            traffic_thread.start()

        for t in range(5, 0, -1):
            traffic_lights[current_road_index].update_light("yellow", countdown_time=t)
            root.update()
            time.sleep(1)

        traffic_lights[current_road_index].update_light("red")
        root.update()

    # Wait for the new data to be fetched
    if new_data_holder:
        traffic_thread.join()  # Ensure data fetching is complete before proceeding
        intensities = new_data_holder[0]

        # Print the data of the next cycle before starting the cycle
        print("\nNext cycle data (updated traffic intensities):")
        for i, point in enumerate(snapped_points):
            road_coords = (point['location']['latitude'], point['location']['longitude'])
            traffic_intensity = intensities[i]
            print(f"Road {road_names[i]}: Coordinates: {road_coords}, Traffic Intensity: {traffic_intensity}")

        sorted_indices = sorted(range(len(intensities)), key=lambda i: intensities[i], reverse=True)

    # Start the next cycle with the updated data immediately
    print("\nStarting next cycle with updated traffic data.")
    root.after(1000, update_traffic_lights, root, road_names, snapped_points, traffic_lights, api_key,
               life_cycle_seconds)


def create_traffic_lights(root, road_names, snapped_points, api_key, life_cycle_seconds):
    traffic_lights = []
    for i, road_name in enumerate(road_names):
        frame = tk.Frame(root)
        frame.pack(pady=10)

        label = tk.Label(frame, text=f"Road {road_name}")
        label.pack()

        traffic_light = TrafficLightGUI(frame)
        traffic_lights.append(traffic_light)

    update_traffic_lights(root, road_names, snapped_points, traffic_lights, api_key, life_cycle_seconds)


def submit(latitude_entry, longitude_entry, box_id_entry, range_entry, life_cycle_entry, max_snap_points_entry):
    latitude = float(latitude_entry.get())
    longitude = float(longitude_entry.get())
    traffic_box_id = box_id_entry.get()
    range_m = float(range_entry.get())  # Now range is taken in meters
    life_cycle_seconds = int(life_cycle_entry.get())
    max_snap_points = int(max_snap_points_entry.get())  # User-defined number of snapped points

    print("Location (Latitude, Longitude):", latitude, longitude)
    print("Traffic Box ID:", traffic_box_id)
    print("Range of Device (in meters):", range_m)
    print("Total Life Cycle (in seconds):", life_cycle_seconds)

    google_maps_url = f"https://www.google.com/maps/@{latitude},{longitude},15z"
    webbrowser.open(google_maps_url)

    snapped_points, num_roads = count_nearby_roads(latitude, longitude, API_KEY, range_m,
                                                   max_snap_points=max_snap_points)

    if num_roads > 0:
        road_names = list(string.ascii_uppercase)[:num_roads]

        # Fetch traffic intensities for each snapped road point
        traffic_intensities = determine_traffic_intensities(snapped_points, API_KEY)

        # Print coordinates and traffic intensity for each road
        print(f"\nFound {num_roads} roads near the specified location:")
        for i, point in enumerate(snapped_points):
            road_coords = (point['location']['latitude'], point['location']['longitude'])
            traffic_intensity = traffic_intensities[i]
            print(f"Road {road_names[i]}: Coordinates: {road_coords}, Traffic Intensity: {traffic_intensity}")

        root = tk.Tk()
        root.title("Traffic Light Simulation")
        create_traffic_lights(root, road_names, snapped_points, API_KEY, life_cycle_seconds)
        root.mainloop()
    else:
        print("No roads found near the specified location.")


def main():
    root = tk.Tk()
    root.title("Traffic Congestion Analysis")

    latitude_label = tk.Label(root, text="Latitude:")
    latitude_label.grid(row=0, column=0, padx=10, pady=5)
    latitude_entry = tk.Entry(root)
    latitude_entry.grid(row=0, column=1, padx=10, pady=5)

    longitude_label = tk.Label(root, text="Longitude:")
    longitude_label.grid(row=1, column=0, padx=10, pady=5)
    longitude_entry = tk.Entry(root)
    longitude_entry.grid(row=1, column=1, padx=10, pady=5)

    box_id_label = tk.Label(root, text="Traffic Box ID:")
    box_id_label.grid(row=2, column=0, padx=10, pady=5)
    box_id_entry = tk.Entry(root)
    box_id_entry.grid(row=2, column=1, padx=10, pady=5)

    range_label = tk.Label(root, text="Range of Device (in meters):")
    range_label.grid(row=3, column=0, padx=10, pady=5)
    range_entry = tk.Entry(root)
    range_entry.grid(row=3, column=1, padx=10, pady=5)

    life_cycle_label = tk.Label(root, text="Total Life Cycle (in seconds):")
    life_cycle_label.grid(row=4, column=0, padx=10, pady=5)
    life_cycle_entry = tk.Entry(root)
    life_cycle_entry.grid(row=4, column=1, padx=10, pady=5)

    max_snap_points_label = tk.Label(root, text="Max Snapped Points(1-4):")
    max_snap_points_label.grid(row=5, column=0, padx=10, pady=5)
    max_snap_points_entry = tk.Entry(root)
    max_snap_points_entry.grid(row=5, column=1, padx=10, pady=5)

    submit_button = tk.Button(root, text="Submit",
                              command=lambda: submit(latitude_entry, longitude_entry, box_id_entry, range_entry,
                                                     life_cycle_entry, max_snap_points_entry))
    submit_button.grid(row=6, columnspan=2, pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()
