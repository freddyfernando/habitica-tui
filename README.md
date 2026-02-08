# Habitica CSV Importer

A simple Python script to bulk import tasks into [Habitica](https://habitica.com) from a CSV file.

## Features

- **Bulk Import**: Import Habits, Dailies, and Todos.
- **Rate Limiting**: Automatically handles Habitica's API rate limits (429 errors) with exponential backoff.
- **Customizable**: Map your CSV columns to Habitica task attributes.

## Prerequisites

- Python 3.6+
- A Habitica account

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/freddyfernando/habitica-importer.git
   cd habitica-importer
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Prepare your CSV**:
   Create a CSV file named `habitica-import.csv` (or use the provided `habitica_import_example.csv` as a template).
   
   **Format:**
   ```csv
   Type,Task Name,Notes,Priority
   Habit,Drink Water,Health: 8 glasses,1.5
   Daily,Check Email,Work,1
   Todo,Finish Report,Due Friday,2
   ```

   - **Type**: `Habit`, `Daily`, or `Todo` (case-insensitive)
   - **Task Name**: The title of the task
   - **Notes**: Extra details (optional)
   - **Priority**: Difficulty level (0.1 = Trivial, 1 = Easy, 1.5 = Medium, 2 = Hard)

2. **Run the script**:
   ```bash
   python3 habitica-importer.py
   ```

3. **Enter Credentials**:
   The script will ask for your **User ID** and **API Token**. You can find these in your [Habitica Settings > API](https://habitica.com/user/settings/api).

## License

MIT
