# TrombINT

TrombINT is a Python package that can fetch profile pictures and student information from the IMT-BS/TSP directory (`trombi.imtbs-tsp.eu`). It uses the `Cas_Connector` package to handle authentication via CAS.

## Installation

This project uses `uv` for dependency management. To add this to your project, use:

```bash
uv add trombint
```

Or, to run it directly from source if you clone the repo:

```bash
uv run trombint --help
```

### Pre-requisites
1. Since we connect to `cas6.imtbs-tsp.eu`, you MUST have a valid IMT-BS/TSP username and password.
2. Create a `.env` file in the root of your working directory using the provided `.env.example` file:

```env
CAS_USERNAME=your_username
CAS_PASSWORD=your_password
```

## CLI Usage

The package exposes a `trombint` command-line application (if configured in your path), or you can run it via `uv run trombint`.

```bash
# Get all information for a specific student locally in the terminal
uv run trombint --name "John Doe"

# Save that student's information into a JSON file
uv run trombint --name "John Doe" --out-json john.json

# Get ONLY the profile picture URL for a specific student
uv run trombint --name "John Doe" --pfp-only

# Download the specific student's profile picture to a local file
uv run trombint --name "John Doe" --download-pfp image.jpg

# Get all students and save their information to output.json, while also downloading all their images to a `photos` directory
uv run trombint --all --out-json output.json --download-pfp photos/
```

### Options CLI :
- `--name "Search Name"` : Searches for someone by exact or partial name.
- `--all` : Fetches information for every student.
- `--pfp-only` : Only output the profile picture link(s) for the matched student(s).
- `--out-json PATH` : Saves the JSON output into a specified file rather than printing to stdout.
- `--download-pfp PATH` : Downloads the returned profile picture(s) directly to the specified path. If multiple students match, the path should be a directory.

## Module Usage

You can also import and use `trombint` as a standard Python module in your own scripts. Simply ensure your `.env` is loaded or your `CAS_USERNAME` and `CAS_PASSWORD` environment variables are properly set.

```python
from trombint import get_students_by_name, get_all_students, get_pfp_by_name, get_all_pfps

# Fetch a single student's complete information
students_info = get_students_by_name("John Doe")
print(students_info)
# Output: [{'nom_complet': 'John Doe', 'uid': '...'}]

# Fetch only the PFP URL
pfp_urls = get_pfp_by_name("John")
print(pfp_urls)

# Fetch all students
all_students = get_all_students()

# Fetch all PFPs as a dictionary { "Name": "URL" }
all_pfps = get_all_pfps()
```

## Disclaimer / Avertissement
> [!WARNING]
> Ce projet a été créé à des fins strictement **éducatives**. L'auteur de ce code décline toute responsabilité quant à l'utilisation qui pourrait être faite de ce programme. L'utilisation de ce script pour récupérer des données personnelles est soumise à la réglementation en vigueur, et il est de la responsabilité de l'utilisateur final de s'y conformer.
