Here is a sample `README.md` file for your FastAPI project:

```markdown
# FastAPI Browser Cookies Processor

This project is a FastAPI application that processes browser cookies from Chrome, Firefox, and Edge, zips the network folder, and allows users to retrieve files based on the owner name. The application also supports authentication for file retrieval.

## Features

- Detects the installed browser (Chrome, Firefox, or Edge).
- Zips the browser's network folder and saves it with the owner name.
- Stores the owner name and file path in a SQLite database.
- Provides routes to retrieve all files for a given owner, requiring a password for access.
- Returns individual file links for a given owner.

## Requirements

- Python 3.7+
- FastAPI
- Uvicorn
- Psutil
- PyCryptodome
- Pydantic

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/fastapi-browser-cookies-processor.git
cd fastapi-browser-cookies-processor
```

2. Install the dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application

To start the FastAPI application, run the following command:

```bash
uvicorn main:app --reload
```

Replace `main` with the name of your Python script if it is different.

## Endpoints

### Process Cookies

#### POST /process-cookies/

Processes the browser's network folder and stores it with the owner's name.

**Request Parameters**:
- `owner_name` (form): The name of the owner.

**Response**:
- `200 OK`: Returns a message indicating successful processing and the file path.

### Get Files for Owner

#### GET /get-file/{owner_name}?password={password}

Retrieves all files for the given owner, packaged into a zip file.

**Request Parameters**:
- `owner_name` (path): The name of the owner.
- `password` (query): The password for authentication. (Required: "282200123Aa?!!!")

**Response**:
- `200 OK`: Returns the zip file for download.
- `403 Forbidden`: If the password is incorrect.
- `404 Not Found`: If the owner is not found.

### Get File Links for Owner

#### GET /get-file-link/{owner_name}?password={password}

Returns links to all files for the given owner.

**Request Parameters**:
- `owner_name` (path): The name of the owner.
- `password` (query): The password for authentication. (Required: "282200123Aa?!!!")

**Response**:
- `200 OK`: Returns a list of file links.
- `403 Forbidden`: If the password is incorrect.
- `404 Not Found`: If the owner is not found.

## Example Usage

### Process Cookies

```bash
curl -X POST "http://127.0.0.1:8000/process-cookies/" -F "owner_name=JohnDoe"
```

### Get Files

```bash
curl -X GET "http://127.0.0.1:8000/get-file/JohnDoe?password=282200123Aa?!!!"
```

### Get File Links

```bash
curl -X GET "http://127.0.0.1:8000/get-file-link/JohnDoe?password=282200123Aa?!!!"
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

```

### Notes

- Replace `https://github.com/yourusername/fastapi-browser-cookies-processor.git` with the actual URL of your GitHub repository.
- Update any specific details according to your project's structure and requirements.

This `README.md` provides an overview of the project, installation instructions, API endpoints, and example usage, making it easy for others to understand and use your FastAPI application.