# SBU-Study-Spot-
Campus study spot finder using busyness level. Students get notified when they are within 100m range of Library/Union/Wang/SAC to report crowd levels in building. algorithm calculate and shows  status (Not Busy/Moderate/Busy) of building reported by users. Created using Python libraries like Streamlit, SQLite, Geopy. Stony Brook University Project

# SeawolfStudy - Study Spot Finder

A location-based web application that helps students find and report the crowd status of study spots on campus in real-time.

## Features

- 📍 Real-time location tracking
- 🎯 Proximity-based notifications
- 📊 Crowd status reporting (Not Busy, Moderately Busy, Busy)
- 🗺️ Interactive campus map
- 👤 User authentication system
- 💾 SQLite database for data persistence

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Installation & Setup

### 1. Download the Project

Download the project folder and extract it to your desired location.

### 2. Navigate to Project Directory

Open your terminal and navigate to the project folder:

```bash
cd path/to/SeawolfStudy
```

Replace `path/to/SeawolfStudy` with the actual path where you downloaded the project.

### 3. Create Virtual Environment

Create a Python virtual environment:

```bash
python3 -m venv venv
```

### 4. Activate Virtual Environment

Activate the virtual environment:

**On macOS/Linux:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

### 5. Install Required Libraries

Install all the necessary dependencies:

```bash
pip install streamlit
pip install pandas
pip install streamlit-card
pip install geopy
pip install streamlit-geolocation
```

Alternatively, if a `requirements.txt` file is provided:

```bash
pip install -r requirements.txt
```

### 6. Run the Application

Start the Streamlit application:

```bash
streamlit run main.py
```

The application should automatically open in your default web browser. If it doesn't, navigate to the URL shown in the terminal (usually `http://localhost:8501`).

## Usage

1. **Sign Up**: Create a new account with your username, email, and password
2. **Login**: Log in with your credentials
3. **Allow Location Access**: Grant location permissions when prompted
4. **View Study Spots**: See all available study spots on the campus map
5. **Report Status**: When near a study spot (within 100m), you'll be prompted to report the crowd status
6. **Check Status**: View real-time crowd status for all study spots in the sidebar

## Study Locations

The app currently tracks the following locations:
- Melville Library
- Student Union
- Wang Center
- SAC (Student Activities Center)

## Database

The application uses SQLite to store:
- User accounts
- Study spot locations
- User responses
- Notification logs

The database file (`seawolfstudy.db`) is automatically created on first run.

## Troubleshooting

### Location Not Working
- Make sure you've granted location permissions in your browser
- Check that you're accessing the app via HTTPS or localhost

### Port Already in Use
If port 8501 is already in use, you can specify a different port:
```bash
streamlit run main.py --server.port 8502
```

### Package Installation Issues
If you encounter issues installing packages, try upgrading pip first:
```bash
pip install --upgrade pip
```

## Deactivating Virtual Environment

When you're done using the application, deactivate the virtual environment:

```bash
deactivate
```

## Notes

- The app requires an active internet connection for geolocation services
- Location accuracy depends on your device's GPS capabilities
- Notification cooldown is set to 30 minutes per location

## Support

For issues or questions, please refer to the project documentation or contact the development team.

---

**Built with Streamlit** | **Made for Stony Brook Students**
