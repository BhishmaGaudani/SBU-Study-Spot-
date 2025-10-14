import streamlit as st
import pandas as pd
from streamlit_card import card
from geopy.distance import geodesic
import datetime
from streamlit_geolocation import streamlit_geolocation
import sqlite3
import hashlib


def init_database():
    conn = sqlite3.connect('seawolfstudy.db', check_same_thread=False)

    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            location_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            radius INTEGER DEFAULT 100,
            current_status TEXT DEFAULT 'No Recent Data',
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')


    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_responses (
            response_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            location_id TEXT NOT NULL,
            status_reported TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (location_id) REFERENCES locations(location_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notification_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            location_id TEXT NOT NULL,
            last_notified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (location_id) REFERENCES locations(location_id)
        )
    ''')

    conn.commit()
    return conn


def initialize_locations(conn):
    cursor = conn.cursor()

    locations = [
        ("library", "Melville Library", 40.9152481, -73.1228800),
        ("union", "Student Union", 40.9171445, -73.1224921),
        ("wang", "Wang Center", 40.9161544, -73.1195538),
        ("sac", "SAC", 40.9142291, -73.1243844)
    ]

    for loc_id, name, lat, lon in locations:
        cursor.execute('''
            INSERT OR IGNORE INTO locations (location_id, name, lat, lon)
            VALUES (?, ?, ?, ?)
        ''', (loc_id, name, lat, lon))

    conn.commit()


if 'db_conn' not in st.session_state:
    st.session_state.db_conn = init_database()
    initialize_locations(st.session_state.db_conn)

conn = st.session_state.db_conn


if "page" not in st.session_state:
    st.session_state.page = "home"
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_location" not in st.session_state:
    st.session_state.user_location = None
if "show_prompt" not in st.session_state:
    st.session_state.show_prompt = False
if "prompt_location" not in st.session_state:
    st.session_state.prompt_location = None
if "prompt_name" not in st.session_state:
    st.session_state.prompt_name = None



def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(username, email, password):
    cursor = conn.cursor()
    try:
        password_hash = hash_password(password)
        cursor.execute('''
            INSERT INTO users (user_id, email, password_hash)
            VALUES (?, ?, ?)
        ''', (username, email, password_hash))
        conn.commit()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError:
        return False, "Username or email already exists"
    except Exception as e:
        return False, "Error: " + str(e)


def authenticate_user(email, password):
    cursor = conn.cursor()
    password_hash = hash_password(password)

    cursor.execute('''
        SELECT user_id FROM users 
        WHERE email = ? AND password_hash = ?
    ''', (email, password_hash))

    result = cursor.fetchone()
    if result:
        return True, result[0]
    return False, None


def get_user_location():
    loc = streamlit_geolocation()

    lat = (loc or {}).get("latitude", None)
    lon = (loc or {}).get("longitude", None)

    if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
        return [float(lat), float(lon)]

    return None


def calculate_distance(user_lat, user_lon, location_lat, location_lon):
    user_coords = (user_lat, user_lon)
    location_coords = (location_lat, location_lon)
    distance = geodesic(user_coords, location_coords).meters
    return distance


def check_proximity(user_location, location_data, radius=100):
    if user_location is None:
        return None

    distance = calculate_distance(
        user_location[0], user_location[1],
        location_data["lat"], location_data["lon"]
    )

    if distance <= radius:
        return location_data["name"]
    return None


def should_notify(user_id, location_id):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT last_notified FROM notification_log
        WHERE user_id = ? AND location_id = ?
        ORDER BY last_notified DESC
        LIMIT 1
    ''', (user_id, location_id))

    result = cursor.fetchone()
    if result:
        last_notified = datetime.datetime.fromisoformat(result[0])
        time_diff = datetime.datetime.now() - last_notified
        if time_diff.total_seconds() < 1800:  # 30 minutes
            return False

    return True


def add_user_response(user_id, location_id, status):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_responses (user_id, location_id, status_reported, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (user_id, location_id, status, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()


def log_notification(user_id, location_id):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO notification_log (user_id, location_id, last_notified)
        VALUES (?, ?, ?)
    ''', (user_id, location_id, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()


def get_recent_responses(location_id):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, status_reported, timestamp
        FROM user_responses
        WHERE location_id = ?
        ORDER BY timestamp DESC
        LIMIT 10
    ''', (location_id,))

    results = cursor.fetchall()
    response_list = []

    for row in results:
        response_list.append({
            'user_id': row[0],
            'status_reported': row[1],
            'timestamp': datetime.datetime.now()
        })

    return response_list


def calculate_status(location_id):
    responses = get_recent_responses(location_id)

    if len(responses) < 1:
        return "No Recent Data"

    most_recent = responses[0]['status_reported']
    return most_recent


def update_location_status(location_id):
    new_status = calculate_status(location_id)

    cursor = conn.cursor()
    cursor.execute('''
        UPDATE locations
        SET current_status = ?, last_updated = ?
        WHERE location_id = ?
    ''', (new_status, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), location_id))
    conn.commit()

    return new_status


def get_all_statuses():
    cursor = conn.cursor()
    cursor.execute('SELECT location_id, current_status FROM locations')

    results = cursor.fetchall()
    status_dict = {}

    for row in results:
        status_dict[row[0]] = row[1]

    return status_dict


def get_all_locations():
    cursor = conn.cursor()
    cursor.execute('SELECT location_id, name, lat, lon FROM locations')

    results = cursor.fetchall()
    locations = []

    for row in results:
        locations.append({
            'id': row[0],
            'name': row[1],
            'lat': row[2],
            'lon': row[3]
        })

    return locations

def go_to_login():
    st.session_state.page = "login"

def go_to_signup():
    st.session_state.page = "signup"

def go_to_home():
    st.session_state.page = "home"

if st.session_state.page in ["home", "login", "signup"]:
    st.markdown("""
        <style>
        .stApp { background: linear-gradient(135deg, #990000, #6B000D); }
        h1 {
            text-align: center;
            font-size: 112px;
            background: linear-gradient(90deg, #1791AD, #BCCF9D);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .stButton > button {
            width: 250px; border-radius: 20px;
            background: linear-gradient(90deg, #1791AD, #002244);
            color: white; font-size: 30px; padding: 20px 40px;
            border: none; cursor: pointer; transition: 0.2s;
            display: block; margin: 0 auto;
        }
        .stButton > button:hover { filter: brightness(2.5); }
        </style>
    """, unsafe_allow_html=True)



def log(email, password):
    success, user_id = authenticate_user(email, password)

    if success:
        st.session_state.user_id = user_id
        st.session_state.page = "app_page"
        st.rerun()
    else:
        st.warning("Login Failed: Invalid email or password.")


if st.session_state.page == "home":
    st.title("SeawolfStudy")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.button("Login", on_click=go_to_login)
        st.button("Signup", on_click=go_to_signup)

elif st.session_state.page == "login":
    st.title("Login")
    email = st.text_input("Email Address")
    password = st.text_input("Password", type="password")
    if st.button("Submit"):
        log(email, password)
    if st.button("⬅ Back"):
        go_to_home()

elif st.session_state.page == "signup":
    st.title("Sign Up")
    userName = st.text_input("Enter Your Unique Username")
    newUserEmail = st.text_input("Email")
    new_pass = st.text_input("New Password", type="password")

    if st.button("Register"):
        success, message = create_user(userName, newUserEmail, new_pass)
        if success:
            st.success(message)
            st.info("Please proceed to the login page.")
        else:
            st.error(message)

    if st.button("⬅ Back"):
        go_to_home()

elif st.session_state.page == "app_page":
    st.markdown(
        """
        <style>
            # .stApp {
            #     background-color: white;
            # }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.title("🎓 SeawolfStudy - Study Spot Finder")

    PLACES = get_all_locations()

    if st.session_state.user_location is None:
        st.session_state.user_location = get_user_location()

    if st.session_state.user_location:
        lat_val = st.session_state.user_location[0]
        lon_val = st.session_state.user_location[1]
        st.success("📍 Your Location: Latitude " + str(round(lat_val, 6)) + ", Longitude " + str(round(lon_val, 6)))
    else:
        st.info("📍 Click 'Get Location' and allow location access to enable proximity notifications.")

    st.markdown("---")

    if st.session_state.user_location and not st.session_state.show_prompt:
        for place in PLACES:
            nearby = check_proximity(st.session_state.user_location, place, radius=100)

            if nearby:
                location_id = place["id"]

                if should_notify(st.session_state.user_id, location_id):
                    st.session_state.show_prompt = True
                    st.session_state.prompt_location = location_id
                    st.session_state.prompt_name = nearby
                    log_notification(st.session_state.user_id, location_id)
                    break

    if st.session_state.show_prompt:
        st.info("📍 You're near " + st.session_state.prompt_name + "!")
        st.write("**How busy is it right now?**")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🟢 Not Busy", use_container_width=True):
                add_user_response(st.session_state.user_id, st.session_state.prompt_location, "Not Busy")
                update_location_status(st.session_state.prompt_location)
                st.session_state.show_prompt = False
                st.success("Thanks for your input!")
                st.rerun()

        with col2:
            if st.button("🟡 Moderately Busy", use_container_width=True):
                add_user_response(st.session_state.user_id, st.session_state.prompt_location, "Moderately Busy")
                update_location_status(st.session_state.prompt_location)
                st.session_state.show_prompt = False
                st.success("Thanks for your input!")
                st.rerun()

        with col3:
            if st.button("🔴 Busy", use_container_width=True):
                add_user_response(st.session_state.user_id, st.session_state.prompt_location, "Busy")
                update_location_status(st.session_state.prompt_location)
                st.session_state.show_prompt = False
                st.success("Thanks for your input!")
                st.rerun()

    elif st.session_state.user_location:

        distances = []
        for place in PLACES:
            dist = calculate_distance(
                st.session_state.user_location[0],
                st.session_state.user_location[1],
                place['lat'],
                place['lon']
            )
            distances.append((place['name'], dist))

        nearest = min(distances, key=lambda x: x[1])

        if nearest[1] > 100:
            distance_text = str(int(nearest[1]))
            place_name = nearest[0]
            st.warning("🚶 You're " + distance_text + "m away from the nearest study spot (" + place_name + "). Get within 100m to report crowd status!")

    with st.sidebar:
        st.title("Study Spot Status")

        statuses = get_all_statuses()

        status_emoji = {
            "Not Busy": "🟢",
            "Moderately Busy": "🟡",
            "Busy": "🔴",
            "No Recent Data": "⚪"
        }

        for place in PLACES:
            location_id = place["id"]
            status = statuses.get(location_id, "No Recent Data")
            emoji = status_emoji.get(status, "⚪")

            card(
                title=place["name"],
                text=status + " " + emoji,
            )

    st.subheader("📍 Campus Map")

    if st.session_state.user_location:
        col_map, col_info = st.columns([2, 1])

        with col_map:
            places_df = pd.DataFrame(PLACES)
            user_df = pd.DataFrame({
                'name': ['📍 You'],
                'lat': [st.session_state.user_location[0]],
                'lon': [st.session_state.user_location[1]]
            })

            all_points = pd.concat([places_df[['name', 'lat', 'lon']], user_df], ignore_index=True)

            st.map(
                data=all_points,
                latitude="lat",
                longitude="lon",
                color="#1e90ff",
                size=8,
                zoom=16,
                use_container_width=True,
                height=500
            )

        with col_info:
            st.markdown("### Distances")
            for place in PLACES:
                distance = calculate_distance(
                    st.session_state.user_location[0],
                    st.session_state.user_location[1],
                    place['lat'],
                    place['lon']
                )
                if distance <= 100:
                    st.markdown("🟢 **" + place['name'] + "**")
                    dist_str = str(int(distance))
                    st.markdown("*" + dist_str + "m - Within range!*")
                elif distance <= 500:
                    st.markdown("🟡 **" + place['name'] + "**")
                    st.markdown("*" + str(int(distance)) + "m away*")
                else:
                    st.markdown("⚪ **" + place['name'] + "**")
                    st.markdown("*" + str(int(distance)) + "m away*")

                st.markdown("---")
    else:
        df_places = pd.DataFrame(PLACES)
        st.map(
            data=df_places,
            latitude="lat",
            longitude="lon",
            color="#ffaa00",
            size=8,
            zoom=15,
            use_container_width=True,
            height=500
        )
        st.warning("📍 Enable location access to see your position and get proximity notifications")