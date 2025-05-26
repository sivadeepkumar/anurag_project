# Excel to JSON Converter

A Flask web application that allows users to upload Excel files and convert them to JSON format.

## Features

- Upload Excel files (.xlsx, .xls)
- Convert Excel data to JSON format
- Preview the JSON data on the web interface
- Save the converted JSON file in the uploads directory

## Setup and Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Run the application:
   ```
   python app.py
   ```

5. Access the application in your web browser:
   ```
   http://localhost:5173
   ```

## Project Structure

```
.
├── app/
│   ├── static/
│   ├── templates/
│   │   └── index.html
│   └── uploads/
├── app.py
├── requirements.txt
└── README.md
```

## Usage

1. Open the web application in your browser
2. Click on the Excel upload box to select your Excel file
3. Click the "Convert Excel to JSON" button
4. View the JSON preview on the right side
5. The JSON file will be saved in the app/uploads directory

## Dependencies

- Flask
- Pandas
- Openpyxl
- Werkzeug 