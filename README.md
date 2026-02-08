# Habitica TUI 🎮

A Ranger-inspired terminal user interface for managing your Habitica tasks.

![Habitica TUI Interface](https://github.com/freddyfernando/habitica-tui/raw/main/screenshot_placeholder.png) *(Add a real screenshot later)*

## Features

- **3-Column Ranger Layout**: Efficient navigation between Categories (left), Task List (center), and Task Details (right).
- **Vim-style Controls**: Navigate with `h/j/k/l`.
- **Interactive Management**: Score, Edit, and Delete tasks directly from the terminal.
- **Robust Import**: Sync tasks from YAML, Markdown (Obsidian checklist style), or CSV.
- **Rich Visuals**: Color-coded task list reflecting task health and Markdown-rendered detail previews.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/freddyfernando/habitica-tui.git
   cd habitica-tui
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your credentials:
   Create a `.env` file or export the following variables:
   ```bash
   export HABITICA_USER_ID="your-user-id"
   export HABITICA_API_TOKEN="your-api-token"
   ```

## Usage

Run the TUI:
```bash
python habitica-importer.py
```

### Shortcuts

| Key | Action |
|-----|--------|
| `j`/`k` | Move up/down in lists |
| `h`/`l` | Switch focus between panes |
| `s` | Score task UP (+) |
| `x` | Score task DOWN (-) |
| `e` | Edit task details |
| `d` | Delete task |
| `i` | Import from file (CSV/YAML/MD) |
| `r` | Refresh task list |
| `q` | Quit |

## License
MIT
