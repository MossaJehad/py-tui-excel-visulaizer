# Excel Data Visualizer (TUI)

A beautiful terminal-based Excel file viewer and data visualizer built with Python and Textual.

## ✨ Features

### 📋 Data Viewing
- Browse and view Excel files (.xlsx, .xls) in your terminal
- Navigate through multiple sheets
- Interactive data table with keyboard navigation
- Clean, modern UI with Tokyo Night color scheme

### 📊 Statistics Panel
- Dataset overview (rows, columns)
- Automatic data type detection
- Summary statistics for numeric columns:
  - Min, Max, Mean, Standard Deviation
- Unique value counts for text columns

### 📈 Visual Charts
- **Numeric Data Visualizations**:
  - Histogram distributions with ASCII bar charts
  - Automatic binning for continuous data

- **Categorical Data Visualizations**:
  - Top 10 value distributions
  - Frequency bar charts
  - Support for multiple categorical columns

## 🚀 Installation

```bash
# Install dependencies
pip install textual pandas openpyxl
```

## 📖 Usage

1. Place your Excel files in the `xlsx/` folder
2. Run the application:
   ```bash
   python app.py
   ```
3. Use arrow keys to navigate and Enter to select

## ⌨️ Keyboard Shortcuts

- `↑/↓` - Navigate lists and tables
- `Enter` - Select file/sheet
- `Tab` - Switch to next tab
- `Shift+Tab` - Switch to previous tab
- `Escape` - Go back to previous screen
- `q` - Quit application

## 📂 Project Structure

```
py-tui-excel-visulaizer/
├── app.py           # Main application
├── xlsx/            # Place your Excel files here
│   └── HR.xlsx      # Example file
└── README.md        # This file
```

## 🎨 Features Detail

### Three-Tab Interface

1. **📋 Data Tab**: View your raw data in an interactive table
2. **📊 Statistics Tab**: See comprehensive statistics and insights
3. **📈 Charts Tab**: Visualize data distributions with ASCII charts

### Smart Data Analysis

The app automatically:
- Detects numeric vs categorical columns
- Generates appropriate visualizations for each data type
- Handles missing values gracefully
- Provides meaningful statistical summaries

## 🛠️ Technical Details

- **Framework**: Textual (Python TUI framework)
- **Data Processing**: Pandas
- **Excel Support**: openpyxl
- **Visualization**: Custom ASCII charts

## 📝 Example

When you open an Excel file, you'll see:
- Raw data in an interactive table
- Statistics showing min/max/mean/std for numeric columns
- Histogram distributions for numeric data
- Top 10 value charts for categorical data

All rendered beautifully in your terminal with a clean, modern interface!

## 🎯 Future Enhancements

Potential improvements:
- Data filtering and sorting
- Export filtered data
- More chart types (line charts, scatter plots)
- Custom color themes
- Search functionality
- Column highlighting

## 📄 License

See LICENSE file for details.
