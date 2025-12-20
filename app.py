from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, ListView, ListItem, DataTable, Label, TabbedContent, TabPane, Input, Button
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on, work
import pandas as pd
import numpy as np
import os
import json
import google.generativeai as genai
from collections import Counter

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

	/* Stats Panel */
	.stats-container {
		height: 100%;
		background: #1a1b26;
		padding: 1 2;
	}

	.stat-card {
		background: #24283b;
		border: solid #414868;
		padding: 1 2;
		margin: 1 0;
	}

	.stat-title {
		color: #7aa2f7;
		text-style: bold;
		margin-bottom: 1;
	}

	.stat-value {
		color: #9ece6a;
		text-style: bold;
	}

	.chart-container {
		background: #1a1b26;
		padding: 1 2;
		border: solid #414868;
		margin: 1 0;
	}

	.chart-title {
		color: #7aa2f7;
		text-style: bold;
		text-align: center;
		margin-bottom: 1;
	}

	TabbedContent {
		height: 100%;
	}

	TabPane {
		padding: 0;
	}
"""

class BarChart(Static):
	"""A simple ASCII bar chart widget."""

	def __init__(self, data: dict, max_bar_length: int = 40):
		super().__init__()
		self.data = data
		self.max_bar_length = max_bar_length

	def render(self) -> str:
		if not self.data:
			return "No data to display"

		max_value = max(self.data.values()) if self.data.values() else 1
		lines = []

		for label, value in self.data.items():
			bar_length = int((value / max_value) * self.max_bar_length) if max_value > 0 else 0
			bar = "█" * bar_length
			lines.append(f"{label:15} │ {bar} {value}")

		return "\n".join(lines)


class StatsPanel(Static):
	"""Statistics panel for numeric columns."""

	def __init__(self, df: pd.DataFrame):
		super().__init__()
		self.df = df

	def render(self) -> str:
		lines = []
		lines.append("📊 [bold cyan]Dataset Statistics[/bold cyan]\n")
		lines.append(f"Rows: [green]{len(self.df)}[/green]")
		lines.append(f"Columns: [green]{len(self.df.columns)}[/green]\n")

		# Numeric columns statistics
		numeric_cols = self.df.select_dtypes(include=[np.number]).columns
		if len(numeric_cols) > 0:
			lines.append("[bold cyan]Numeric Columns:[/bold cyan]")
			for col in numeric_cols[:5]:  # Show first 5 numeric columns
				try:
					lines.append(f"\n[yellow]{col}[/yellow]")
					lines.append(f"  Min:  {self.df[col].min():.2f}")
					lines.append(f"  Max:  {self.df[col].max():.2f}")
					lines.append(f"  Mean: {self.df[col].mean():.2f}")
					lines.append(f"  Std:  {self.df[col].std():.2f}")
				except:
					pass

		# Categorical columns
		cat_cols = self.df.select_dtypes(include=['object']).columns
		if len(cat_cols) > 0:
			lines.append(f"\n[bold cyan]Text Columns:[/bold cyan] {len(cat_cols)}")
			for col in cat_cols[:3]:  # Show first 3 categorical columns
				unique_count = self.df[col].nunique()
				lines.append(f"  {col}: {unique_count} unique values")

		return "\n".join(lines)


class CategoryChart(Static):
	"""Display top categories as a bar chart."""

	def __init__(self, df: pd.DataFrame, column: str, top_n: int = 10):
		super().__init__()
		self.df = df
		self.column = column
		self.top_n = top_n

	def render(self) -> str:
		if self.column not in self.df.columns:
			return f"Column '{self.column}' not found"

		value_counts = self.df[self.column].value_counts().head(self.top_n)

		lines = []
		lines.append(f"[bold cyan]Top {self.top_n} - {self.column}[/bold cyan]\n")

		max_value = value_counts.max() if len(value_counts) > 0 else 1
		max_bar_length = 30

		for label, count in value_counts.items():
			bar_length = int((count / max_value) * max_bar_length) if max_value > 0 else 0
			bar = "█" * bar_length
			label_str = str(label)[:20]  # Truncate long labels
			lines.append(f"{label_str:20} │ {bar} {count}")

		return "\n".join(lines)


class SelectionListItem(ListItem):
	"""A custom ListItem that keeps track of the value it represents."""
	def __init__(self, label_text: str) -> None:
		super().__init__()
		self.label_text = label_text

	def compose(self) -> ComposeResult:
		yield Label(self.label_text)

class ApiKeyScreen(Screen):
	"""Screen to enter Google API Key."""

	def compose(self) -> ComposeResult:
		with Container(classes="menu-container"):
			yield Label("🔑 Enter Google API Key", classes="title")
			yield Label("A free API key is required for AI features.", classes="instruction")
			yield Input(placeholder="AIzaSy...", id="api-key-input", password=True)
			yield Button("Submit", id="submit-key", variant="primary")
			yield Label("Get one at: https://aistudio.google.com/app/apikey", classes="instruction")

	@on(Button.Pressed, "#submit-key")
	def submit_key(self):
		key = self.query_one("#api-key-input").value
		if key:
			os.environ["GOOGLE_API_KEY"] = key
			self.app.pop_screen()
			self.app.push_screen(FileSelectionScreen())

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
	"""Screen to view the Excel data with statistics and visualizations."""

	def __init__(self, file_path: str, sheet_name: str):
		super().__init__()
		self.file_path = file_path
		self.sheet_name = sheet_name
		self.df = None

	def compose(self) -> ComposeResult:
		with TabbedContent():
			with TabPane("📋 Data", id="data-tab"):
				yield DataTable(id="data-table")

			with TabPane("📊 Statistics", id="stats-tab"):
				with VerticalScroll(classes="stats-container"):
					yield Static(id="stats-panel")

			with TabPane("📈 Charts", id="charts-tab"):
				with VerticalScroll(classes="stats-container"):
					yield Static(id="charts-panel")

		yield Footer()

	def on_mount(self):
		self.title = f"{os.path.basename(self.file_path)} - {self.sheet_name}"
		self.load_data()

	@work(thread=True)
	def load_data(self):
		try:
			self.df = pd.read_excel(self.file_path, sheet_name=self.sheet_name)

			# Prepare data for display
			df_display = self.df.fillna("")
			columns = [str(col) for col in df_display.columns]
			rows = df_display.values.tolist()
			rows = [[str(cell) for cell in row] for row in rows]

			self.app.call_from_thread(self.populate_ui, columns, rows)
		except Exception as e:
			self.app.call_from_thread(self.show_error, str(e))

	def populate_ui(self, columns, rows):
		# Populate data table
		table = self.query_one("#data-table", DataTable)
		table.add_columns(*columns)
		table.add_rows(rows)
		table.focus()

		# Populate statistics
		self.populate_statistics()

		# Populate charts
		self.populate_charts()

	def populate_statistics(self):
		"""Populate the statistics panel."""
		stats_panel = self.query_one("#stats-panel", Static)
		stats_widget = StatsPanel(self.df)
		stats_panel.update(stats_widget.render())

	def populate_charts(self):
		"""Populate the charts panel."""
		charts_panel = self.query_one("#charts-panel", Static)
		charts_panel.update("🤖 Asking AI for visualization suggestions...\n(This might take a few seconds)")
		self.generate_ai_charts()

	@work(thread=True)
	def generate_ai_charts(self):
		api_key = os.environ.get("GOOGLE_API_KEY")
		if not api_key:
			self.app.call_from_thread(self.show_error, "No API Key found")
			return

		try:
			genai.configure(api_key=api_key)
			model = genai.GenerativeModel('gemini-1.5-flash')

			# Prepare summary
			buffer = []
			buffer.append("Columns: " + ", ".join([str(c) for c in self.df.columns]))

			# Sample data (first 5 rows)
			sample_data = self.df.head(5).to_string()
			buffer.append(f"Sample data:\n{sample_data}")

			summary = "\n".join(buffer)

			prompt = f"""
			Analyze this dataset summary:
			{summary}

			Suggest 3 visualizations to understand this data.
			Return ONLY a valid JSON array of objects. Do not use markdown code blocks.
			Each object must have:
			- "title": string
			- "type": "bar" or "pie" or "histogram"
			- "column": string (for histogram/pie) or "x_column" and "y_column" (for bar)
			- "explanation": short string

			For 'bar', use a categorical column for x_column and numeric for y_column.
			For 'pie', use a categorical column.
			For 'histogram', use a numeric column.
			"""

			response = model.generate_content(prompt)
			text = response.text.strip()
			# Remove markdown code blocks if present
			if text.startswith("```json"):
				text = text[7:]
			if text.startswith("```"):
				text = text[3:]
			if text.endswith("```"):
				text = text[:-3]

			suggestions = json.loads(text)
			self.app.call_from_thread(self.render_ai_charts, suggestions)

		except Exception as e:
			self.app.call_from_thread(self.show_error, f"AI Error: {str(e)}")

	def render_ai_charts(self, suggestions):
		charts_panel = self.query_one("#charts-panel", Static)
		lines = []
		lines.append("[bold cyan]🤖 AI Suggested Visualizations[/bold cyan]\n")

		for item in suggestions:
			try:
				lines.append(f"\n[bold yellow]{item.get('title', 'Chart')}[/bold yellow]")
				lines.append(f"[italic]{item.get('explanation', '')}[/italic]")

				chart_type = item.get("type")

				if chart_type == "bar":
					x_col = item.get("x_column")
					y_col = item.get("y_column")
					if x_col in self.df.columns and y_col in self.df.columns:
						# Group by x and sum y
						data = self.df.groupby(x_col)[y_col].sum().head(10).to_dict()
						chart = BarChart(data)
						lines.append(chart.render())
					else:
						lines.append(f"[red]Columns {x_col} or {y_col} not found[/red]")

				elif chart_type == "pie":
					col = item.get("column")
					if col in self.df.columns:
						chart = CategoryChart(self.df, col)
						lines.append(chart.render())
					else:
						lines.append(f"[red]Column {col} not found[/red]")

				elif chart_type == "histogram":
					col = item.get("column")
					if col in self.df.columns:
						try:
							hist, bins = np.histogram(self.df[col].dropna(), bins=10)
							max_hist = max(hist) if len(hist) > 0 else 1
							for i, count in enumerate(hist):
								bar_length = int((count / max_hist) * 30) if max_hist > 0 else 0
								bar = "█" * bar_length
								bin_label = f"{bins[i]:.1f}-{bins[i+1]:.1f}"
								lines.append(f"{bin_label:15} │ {bar} {count}")
						except:
							lines.append("[red]Could not create histogram[/red]")
					else:
						lines.append(f"[red]Column {col} not found[/red]")

				lines.append("\n" + "─" * 40)

			except Exception as e:
				lines.append(f"[red]Error rendering chart: {e}[/red]")

		charts_panel.update("\n".join(lines))

	def show_error(self, error):
		# Show error in a label or modal
		pass


class ExcelViewerApp(App):
	CSS = CSS
	BINDINGS = [
		("q", "quit", "Quit"),
		("escape", "pop_screen", "Back"),
		("tab", "next_tab", "Next Tab"),
		("shift+tab", "previous_tab", "Previous Tab")
	]

	def on_mount(self):
		if not os.environ.get("GOOGLE_API_KEY"):
			self.push_screen(ApiKeyScreen())
		else:
			self.push_screen(FileSelectionScreen())

	def action_pop_screen(self):
		if len(self.screen_stack) > 1:
			self.pop_screen()
		else:
			self.exit()

	def action_next_tab(self):
		"""Switch to the next tab."""
		tabbed_content = self.screen.query(TabbedContent).first()
		if tabbed_content:
			tabbed_content.action_next_tab()

	def action_previous_tab(self):
		"""Switch to the previous tab."""
		tabbed_content = self.screen.query(TabbedContent).first()
		if tabbed_content:
			tabbed_content.action_previous_tab()

if __name__ == "__main__":
	ExcelViewerApp().run()
