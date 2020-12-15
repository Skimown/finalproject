"""
Course: CS230 HB3
Creator: Simon Chen
Description: Creates an online interface for the user to browse and book
Airbnb options based on a record of listings in Cambridge in CSV format
This program is created as the final project of the CS230 HB3 course of
Bentley University during the Fall 2020 semester. As such, it has been
created with respect to academic integrity. Specifically, all code
present in this program is written by me, Simon Chen, and this code
has not been shared with any other students.
"""

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import datetime
import math
import os
from haversine import haversine
from csv import writer

zero_day = datetime.date(2020,12,17) # The day before the "first day" that users can book a listing
max_days_ahead = 90 # Number of days ahead of "zero day" to keep track of listings

landmark_coordinates = { # Dictionary of the coordinates of specific landmarks
    "MIT Museum": [42.362379992017246, -71.0975875169152],
    "Bunker Hill Monument": [42.376488816810344, -71.06080858807873],
    "USS Constitution": [42.37270689222049, -71.05660445924268],
    "Museum of Science": [42.367945830321005, -71.07053522114052],
    "Harvard Museum of Natural History": [42.37861316322023, -71.11561124575104]
}

def read_listing_data():
    """
    Reads the Airbnb listings CSV file assuming it's in the same folder
    as main.py, or asks the user to input the directory of the CSV file
    if it's not found.
    """
    try:
        data = pd.read_csv("airbnb_cambridge_listings_20201123.csv")
    except:
        csv_directory = st.text_input("Please enter the directory of the CSV file:")
        # Adds .csv file extension to directory in case user forgets
        if csv_directory[-4:] != ".csv":
            csv_directory = csv_directory + ".csv"
        data = pd.read_csv(csv_directory)
    data.rename(columns = {"id": "ID", "name": "Name", "host_name": "Host Name", "neighbourhood": "Neighborhood", "latitude": "lat", "longitude": "lon", "room_type": "Room Type", "price": "Price", "minimum_nights": "Minimum Nights"}, inplace = True)
    return data

def read_booking_data(df_id):
    """
    Reads the booking CSV file assuming it's in the same folder as main.py,
    or creates a new CSV file using the provided dataframe if no existing file
    is detected.
    """
    try:
        data = pd.read_csv("booking.csv").set_index("id")
    except:
        booking_dict = {}
        id_list = []
        for id in df_id:
            id_list.append(id)
        booking_dict["id"] = id_list
        for day in range(1, max_days_ahead + 1):
            booking_dict[str(day)] = [""] * len(id_list)
        data = pd.DataFrame(booking_dict).set_index("id")
        data.to_csv("booking.csv")
    return data

def filtering(df_backend):
    """
    Creates Streamlit user interface for filtering listings to the user's parameters.
    """
    df_frontend = df_backend.drop(df_backend.columns[[2,4,11,12,13,14,15]],axis = 1)
    min_price_per_night = int(st.sidebar.text_input("Minimum price per night",1))
    max_price_per_night = int(st.sidebar.text_input("Maximum price per night",3000))
    minimum_nights_string = st.sidebar.selectbox("Minimum nights",["Any","1","2","3","4","5","6","7","8","9","10+"])
    # If minimum nights is "Any", make it all values from 1 to 365
    if minimum_nights_string == "Any":
        minimum_nights = []
        for x in range(1, 366):
            minimum_nights.append(x)
    # If minimum nights is "10+", make it all values from 10 to 365
    elif minimum_nights_string == "10+":
        minimum_nights = []
        for x in range(10, 366):
            minimum_nights.append(x)
    else:
        minimum_nights = [int(minimum_nights_string)]
    neighborhoods = st.sidebar.multiselect("Neighborhoods",["Agassiz","Area 2/MIT","Cambridge Highlands","Cambridgeport","East Cambridge","Mid-Cambridge","Neighborhood Nine","North Cambridge","Riverside","Strawberry Hill","The Port","Wellington-Harrington","West Cambridge"])
    # If neighborhood list is empty, make it equal to all possible neighborhoods
    if neighborhoods == []:
        neighborhoods = ["Agassiz","Area 2/MIT","Cambridge Highlands","Cambridgeport","East Cambridge","Mid-Cambridge","Neighborhood Nine","North Cambridge","Riverside","Strawberry Hill","The Port","Wellington-Harrington","West Cambridge"]
    room_types = st.sidebar.multiselect("Room types",["Entire home/apt","Private room","Shared room"])
    # If room types list is empty, make it equal to all possible room types
    if room_types == []:
        room_types = ["Entire home/apt","Private room","Shared room"]
    custom_lat = st.sidebar.text_input("Custom location latitude", 0)
    custom_lon = st.sidebar.text_input("Custom location longitude", 0)
    landmark_coordinates.update({"Custom Location": [custom_lat,custom_lon]})
    for landmark, value in landmark_coordinates.items():
        df_frontend["Distance to " + landmark] = distance_calculator(landmark,df_backend)
    df_frontend_filtered = df_frontend[df_frontend["Price"].isin(range(min_price_per_night,max_price_per_night)) & df_frontend["Minimum Nights"].isin(minimum_nights) & df_frontend["Neighborhood"].isin(neighborhoods) & df_frontend["Room Type"].isin(room_types)]
    return df_frontend_filtered

def distance_calculator(landmark, df):
    """
    Calculates the distance between the listing and designated location
    based on GPS coordinates
    """
    landmark_coordinate = (float(landmark_coordinates[landmark][0]),float(landmark_coordinates[landmark][1]))
    latitude_list = df["lat"].values.tolist()
    longitude_list = df["lon"].values.tolist()
    distance_list = []
    for x in range(0, len(latitude_list)):
        listing_coordinate = [latitude_list[x],longitude_list[x]]
        distance = haversine(listing_coordinate,landmark_coordinate) * 0.6213712
        distance_list.append(distance)
    return distance_list

def neighborhood_graphing(df_frontend_filtered):
    """
    Bar graph of remaining listings based on neighborhood
    """
    neighborhood_list = df_frontend_filtered["Neighborhood"].to_list()
    neighborhood_bins = {
        "Agassiz": 0,
        "Area 2/MIT": 0,
        "Cambridge Highlands": 0,
        "Cambridgeport": 0,
        "East Cambridge": 0,
        "Mid-Cambridge": 0,
        "Neighborhood Nine": 0,
        "North Cambridge": 0,
        "Riverside": 0,
        "Strawberry Hill": 0,
        "The Port": 0,
        "Wellington-Harrington": 0,
        "West Cambridge": 0
    }
    for neighborhood in neighborhood_list:
        neighborhood_bins[neighborhood] += 1
    plt.bar(neighborhood_bins.keys(),neighborhood_bins.values(),color="#FFD700")
    plt.title("Listing Neighborhoods")
    plt.xticks(rotation=90)
    st.pyplot()

def price_graphing(df_frontend_filtered):
    """
    Bar graph of remaining listings based on price per night
    """
    price_list = df_frontend_filtered["Price"].to_list()
    price_bins = {
        "0-50": 0,
        "50-100": 0,
        "100-150": 0,
        "150-200": 0,
        "200-250": 0,
        "250-300": 0,
        "300+": 0,
    }
    for price in price_list:
        if price >= 300:
            price_bins["300+"] += 1
        elif price >= 250:
            price_bins["250-300"] += 1
        elif price >= 200:
            price_bins["200-250"] += 1
        elif price >= 150:
            price_bins["150-200"] += 1
        elif price >= 100:
            price_bins["100-150"] += 1
        elif price >= 50:
            price_bins["50-100"] += 1
        else:
            price_bins["0-50"] += 1
    plt.bar(price_bins.keys(), price_bins.values(),color=["#FF0000","#FF7F00","#FFFF00","#00FF00","#0000FF","#4B0082","#9400D3"])
    plt.title("Price per night")
    st.pyplot()

def room_graphing(df_frontend_filtered):
    """
    Bar graph of remaining listings based on room type
    """
    room_list = df_frontend_filtered["Room Type"].to_list()
    room_bins = {
        "Entire home/apt": 0,
        "Private room":0,
        "Shared room":0
    }
    for room in room_list:
        room_bins[room] += 1
    plt.pie(labels=room_bins.keys(), x=room_bins.values(),autopct="%1.0f%%")
    plt.title("Room Types")
    st.pyplot()

def booking(df_booking,df_backend):
    """
    User interface and verification process for reserving an Airbnb.
    Also handles customer information retrieval and creation.
    """
    listing_id = st.text_input("Listing ID")
    start_date = st.date_input("Start of Reservation")
    end_date = st.date_input("End of Reservation")
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    email = st.text_input("Email Address")
    phone = st.text_input("Phone Number")
    if st.button("Reserve"):
        available = True
        if end_date < start_date:
            st.error("End date can't be before start date")
        elif start_date < datetime.date.today():
            st.error("Can't reserve in the past")
        elif (start_date < zero_day) or (end_date < zero_day):
            st.error("Reservation can't be made before 'zero day': " + str(zero_day))
        elif ((end_date - zero_day).days > 90):
            st.error("Too far into the future")
        elif int(listing_id) not in list(df_booking.index.values):
            st.error("Invalid listing ID")
        elif (email.count("@") == 0) or (email.count(".") == 0):
            st.error("Invalid email address")
        elif email.rfind("@") > email.rfind("."):
            st.error("Invalid email address")
        elif len(phone) != 10 or not phone.isdigit():
            st.error("Invalid phone number")
        else:
            # Booking info valid, checking availability
            row = list(df_booking.loc[int(listing_id)])
            for day in range((start_date - zero_day).days - 1, (end_date - zero_day).days + 1):
                if not math.isnan(row[day]):
                    available = False
            if available:
                # Availability confirmed, booking
                new_log = [first_name, last_name, email, phone, listing_id, start_date.strftime("%d-%b-%Y"), end_date.strftime("%d-%b-%Y")]
                write_to_logs(new_log)
                df_booking_new = df_booking.copy(deep=True)
                for day in range((start_date - zero_day).days, (end_date - zero_day).days + 1):
                    df_booking_new.loc[int(listing_id),str(day)] = 0
                os.remove("booking.csv")
                df_booking_new.to_csv("booking.csv")
                st.success("Reservation successful!")
            else:
                st.warning("Reservation unavailable. Please select another listing or timeframe.")

def write_to_logs(new_log):
    """
    Creates a new CSV file, or appends to an existing one, with booking
    information
    """
    try:
        file = open("log.txt", "a")
    except:
        file = open("log.txt", "w")
        file.close()
        file = open("log.txt", "a")
    file.write(f"{new_log[0]:<15}\t{new_log[1]:<20}\t{new_log[2]:<25}\t{new_log[3]:<12}\t{new_log[4]:<8}\t{new_log[5]:<20}\t{new_log[6]:<20}\n")
    file.close()

def main():
    # Backend dataframe serves as original copy of retrieved data regardless of user filtering
    df_backend = read_listing_data()
    df_booking = read_booking_data(df_backend["ID"])
    st.title("Look for your ideal Cambridge Airbnb!")
    df_frontend_filtered = filtering(df_backend)
    st.dataframe(df_frontend_filtered)
    st.set_option('deprecation.showPyplotGlobalUse', False)
    price_graphing(df_frontend_filtered)
    neighborhood_graphing(df_frontend_filtered)
    room_graphing(df_frontend_filtered)
    st.title("Book your Airbnb here!")
    booking(df_booking,df_backend)


main()
