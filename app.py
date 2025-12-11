from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, ListView, ListItem, DataTable, Label
from textual.containers import Container
from textual import on, work
import pandas as pd
import os

# Minimalist App Theme (Tokyo Night inspired)
CSS = """
Screen {
    align: center middle;
    background: #1a1b26;
    color: #a9b1d6;
}

Header {
    background: #16161e;
    color: #7aa2f7;
    height: 3;
    content-align: center middle;
    text-style: bold;
}

Footer {
    background: #16161e;
    color: #565f89;
    height: 1;
}

/* Menu Container - Centered Card */
.menu-container {
    width: 60%;
    height: auto;
    max-height: 80%;
    border: wide #7aa2f7;
    background: #24283b;
    padding: 1 2;
    box-sizing: border-box;
}

.title {
    text-align: center;
    color: #7aa2f7;
    text-style: bold;
    margin-bottom: 2;
    padding-bottom: 1;
    border-bottom: solid #414868;
}

/* List View Styling */
ListView {
    height: auto;
    max-height: 20;
    border: none;
    scrollbar-gutter: stable;
}

ListItem {
    padding: 1 2;
    background: #24283b;
    color: #c0caf5;
    border-left: solid #24283b; /* Invisible border for alignment */
}

ListItem:hover {
    background: #292e42;
}

ListItem.-highlight {
    background: #414868;
    color: #7aa2f7;
    text-style: bold;
    border-left: wide #7aa2f7; /* Accent border on selected */
}

/* DataTable Styling */
DataTable {
    background: #1a1b26;
    border: none;
}

DataTable > .datatable--header {
    background: #414868;
    color: #7aa2f7;
    text-style: bold;
}

DataTable > .datatable--cursor {
    background: #7aa2f7;
    color: #1a1b26;
}

/* Helper Messages */
.message {
    text-align: center;
    color: #eb4d4b;
    margin: 2;
}

.instruction {
    text-align: center;
    color: #565f89;
    margin-top: 1;
    text-style: italic;
}
"""

class SelectionListItem(ListItem):
    """A custom ListItem that keeps track of the value it represents."""
    def __init__(self, label_text: str) -> None:
        super().__init__()
        self.label_text = label_text

    def compose(self) -> ComposeResult:
        yield Label(self.label_text)

class FileSelectionScreen(Screen):
    """Screen to select an Excel file from the ./xlsx directory."""

    def compose(self) -> ComposeResult:
        folder = "xlsx"
        if not os.path.exists(folder):
            os.makedirs(folder)

        files = sorted([f for f in os.listdir(folder) if f.endswith(".xlsx") or f.endswith(".xls")])
        self.files = files

        with Container(classes="menu-container"):
            yield Label("📁 Select File", classes="title")

            if not files:
                yield Label("No Excel files found!", classes="message")
                yield Label(f"Please place your .xlsx files in the '{folder}' folder.", classes="instruction")
                yield Label("Press Ctrl+C to exit.", classes="instruction")
            else:
                yield ListView(
                    *[SelectionListItem(f) for f in files],
                    id="file-list"
                )
                yield Label("▲/▼ to Navigate • Enter to Select", classes="instruction")

        yield Footer()

    @on(ListView.Selected)
    def select_file(self, event: ListView.Selected):
        # Access the custom attribute directly from our custom ListItem
        if isinstance(event.item, SelectionListItem):
            selected_file = event.item.label_text
            file_path = os.path.join("xlsx", selected_file)
            self.app.push_screen(SheetSelectionScreen(file_path))


class SheetSelectionScreen(Screen):
    """Screen to select a sheet from the chosen Excel file."""

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path

    def compose(self) -> ComposeResult:
        with Container(classes="menu-container"):
            yield Label(f"📄 Select Sheet\n{os.path.basename(self.file_path)}", classes="title")
            yield ListView(id="sheet-list")
            yield Label("Loading sheets...", id="loading-msg", classes="instruction")
        yield Footer()

    def on_mount(self):
        self.load_sheets()

    @work(thread=True)
    def load_sheets(self):
        try:
            xl = pd.ExcelFile(self.file_path)
            sheets = xl.sheet_names
            # Sort sheets? Optional, but often safe to keep original order for Excel.

            self.app.call_from_thread(self.update_list, sheets)
        except Exception as e:
            self.app.call_from_thread(self.show_error, str(e))

    def update_list(self, sheets):
        list_view = self.query_one("#sheet-list", ListView)
        self.query_one("#loading-msg").remove()

        for sheet in sheets:
            list_view.append(SelectionListItem(sheet))

        if not sheets:
             self.mount(Label("No sheets found.", classes="message"))
             # Focus logic might be needed if list is empty, but textual handles empty list nav gracefully usually.
        else:
            list_view.focus()

    def show_error(self, error):
        self.query_one("#loading-msg").update(f"Error: {error}")

    @on(ListView.Selected)
    def select_sheet(self, event: ListView.Selected):
        if isinstance(event.item, SelectionListItem):
            selected_sheet = event.item.label_text
            self.app.push_screen(DataViewerScreen(self.file_path, selected_sheet))


class DataViewerScreen(Screen):
    """Screen to view the Excel data."""

    def __init__(self, file_path: str, sheet_name: str):
        super().__init__()
        self.file_path = file_path
        self.sheet_name = sheet_name

    def compose(self) -> ComposeResult:
        # yield Header()
        yield DataTable()
        yield Footer()

    def on_mount(self):
        self.title = f"{os.path.basename(self.file_path)} - {self.sheet_name}"
        self.load_data()

    @work(thread=True)
    def load_data(self):
        table = self.query_one(DataTable)
        try:
            df = pd.read_excel(self.file_path, sheet_name=self.sheet_name)
            df = df.fillna("") # Handle NaNs

            # Prepare data for DataTable
            columns = [str(col) for col in df.columns]
            rows = df.values.tolist()
            # Convert all cells to strings for display safety
            rows = [[str(cell) for cell in row] for row in rows]

            self.app.call_from_thread(self.populate_table, table, columns, rows)
        except Exception as e:
             # In a real app we might want to pop a modal or show error
             pass

    def populate_table(self, table, columns, rows):
        table.add_columns(*columns)
        table.add_rows(rows)
        table.focus()


class ExcelViewerApp(App):
    CSS = CSS
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("escape", "pop_screen", "Back")
    ]

    def on_mount(self):
        self.push_screen(FileSelectionScreen())

    def action_pop_screen(self):
        if len(self.screen_stack) > 1:
            self.pop_screen()
        else:
            self.exit()

if __name__ == "__main__":
    ExcelViewerApp().run()
