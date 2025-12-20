
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
