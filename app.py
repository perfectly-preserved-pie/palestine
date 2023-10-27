from dash import Dash, dcc, html, no_update, ctx
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from loguru import logger
import dash
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import pandas as pd
import uuid

external_stylesheets = [
  dbc.icons.BOOTSTRAP,
  dbc.icons.FONT_AWESOME,
  dbc.themes.DARKLY,
  "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.2/dbc.min.css", # https://github.com/AnnMarieW/dash-bootstrap-templates#dbccss--stylesheet

]

# Read the translated data from the Parquet file
df = pd.read_parquet('translated.parquet')

# Generate a unique ID for each row
df['uuid'] = [str(uuid.uuid4()) for _ in range(len(df))]

app = Dash(
  __name__, 
  external_stylesheets=external_stylesheets,
  external_scripts=[
    # Plausible analytics
    {
      'src': "https://plausible.automateordie.io/js/plausible.js",
      'data-domain': "palestine.automateordie.io",
      'defer': True,
      'type': 'application/javascript'
    },
  ],
  use_pages=False,
  # Because we're displaying tab content dynamically, we need to suppress callback exceptions
  # https://dash.plotly.com/callback-gotchas#callbacks-require-all-inputs-and-states-to-be-rendered-on-the-page
  suppress_callback_exceptions=True, 
  # Add meta tags for mobile devices
  # https://community.plotly.com/t/reorder-website-for-mobile-view/33669/5?
  meta_tags = [
    {"name": "viewport", "content": "width=device-width, initial-scale=1"}
  ],
)

# Set the page title
app.title = "Victims of the Israeli Aggression on the Gaza Strip during October 7-26, 2023"
app.description = "A searchable and sortable table of all Palestenian deaths during xxxxxx"

title_card = dbc.Card(
  [
    html.H3("Victims of the Israeli Aggression on the Gaza Strip during October 7-26, 2023", className="card-title"),
    html.I("Free Palestine 🇵🇸", style={"margin-bottom": "10px"}),
    html.P(
      "This is a mobile-friendly searchable, sortable, and filterable table of all Palestinian deaths during the latest violence.",
      style = {"margin-bottom": "0px"}
    ),
    html.P(
      "Clicking on anywhere on a row will display the selected martyr's information.",
      style = {"margin-bottom": "0px"}
    ),
    html.I( # use a GitHub icon for my repo
      className="bi bi-github",
      style = {
        "margin-right": "5px",
        "margin-left": "0px"
      },
    ),
    html.A("GitHub", href='https://github.com/perfectly-preserved-pie/palestine', target='_blank'),
  ],
  body = True
)

tabs = dcc.Tabs(
  id="tabs",
  value='/',
  children=[
    dcc.Tab(label='October 7th-26th', value='/'),
    dcc.Tab(label='To be continued...', value='/ep2'),
    dcc.Tab(label='Yep', value='/ep3'),
  ],
)

# Create a modal to display the selected enemy stats
# The modal will be populated by the callback below
modal = dbc.Modal(
  [
    dbc.ModalHeader("Selected Martyr Information"),
    dbc.ModalBody(id="modal-content"),
    dbc.ModalFooter(
        dbc.Button("Close", id="close", className="ml-auto", n_clicks=0)
    ),
  ],
  id="modal",
  is_open=False,
)

# For Gunicorn
server = app.server

app.layout = html.Div(
  [
  dcc.Location(id='url', refresh=False),
  dcc.Store(id='clicked-cell-unique-value'),
  html.Div(title_card),
  html.Div([
    dbc.Button("October 7th-26th", id='btn-ep1', className="mr-2"),
    dbc.Button("Episode II", id='btn-ep2', className="mr-2"),
    dbc.Button("Episode III", id='btn-ep3', className="mr-2"),
  ],
  style={'flex': '0 0 auto'},
  ),
  html.Div(id='grid-container', style={'flex': '1 1 auto', 'overflow-x': 'scroll', 'overflow-y': 'auto'}),
  modal,
  # Add a hidden grid in the initial layout
  html.Div(dag.AgGrid(id='grid'), style={'display': 'none'}),
  ],
  # Set the flexbox direction to column
  # This will make the grid fill the entire page
  style={
    'display': 'flex',
    'flexDirection': 'column',
    'height': '100vh'
  },
)


# Create a function to generate the column definitions based on the dataframe
def generate_column_defs(df):
  # Determine if a column is numeric based on a sampling of 100 values from the column
  # I did this way because I'm too lazy to properly cast dtypes for the 30+ columns across all 3 episode dataframes
  def is_numeric_col(df, column_name):
    # If dtype is already numeric, return True
    if pd.api.types.is_numeric_dtype(df[column_name].dtype):
      return True
    # If dtype is object, sample some rows and test if they can be converted to numbers
    non_na_values = df[column_name].dropna() # Drop NA values
    sample_values = non_na_values.sample(min(100, len(non_na_values))).tolist()
    try:
      # Try converting the sample values to numbers
      [float(x) for x in sample_values]
      return True
    except ValueError:
      # If conversion fails, it's not a numeric column
      return False

  # Extracts the starting number from a cell's content, especially if the content represents a range like "100-200"
  # This is used to sort the numeric columns properly
  def get_value_getter(column_name):
    if is_numeric_col(df, column_name):
      return {"function": f"return params.data.{column_name} && params.data.{column_name}.split('-')[0] ? Number(params.data.{column_name}.split('-')[0]) : null"}
    else:
      return None
  
  # Create the column definitions
  # Both the Name and English Name columns are special because they're pinned to the left
  column_defs = [
        {
        "field": "Name",  # Set the field to "Name" for the Name column
        "minWidth": 150,  # Set a minimum width for the Name column
        "pinned": "left",  # Pin the Name column to the left
        "resizable": True,
        "sortable": True,
        "type": "textColumn",
        "filter": "agTextColumnFilter",
        "floatingFilter": True,
        "floatingFilterComponentParams": {"filterPlaceholder": "Search..."},
        "suppressMenu": True
        },
        {
        "field": "English Name",  # Set the field to "English Name" for the English Name column
        "minWidth": 150,  # Set a minimum width for the English Name column
        "pinned": "left",  # Pin the English Name column to the left
        "resizable": True,
        "sortable": True,
        "type": "textColumn",
        "filter": "agTextColumnFilter",
        "floatingFilter": True,
        "floatingFilterComponentParams": {"filterPlaceholder": "Search..."},
        "suppressMenu": True
        }
    ]

  # Add other columns except the "Name" or "uuid" column
  for i in df.columns:
    if i not in ["Name", "uuid", "English Name"]:
      column_def = {
        "field": i,
        "filter": "agNumberColumnFilter" if is_numeric_col(df, i) else "agTextColumnFilter",
        "floatingFilter": True,
        "floatingFilterComponentParams": {"suppressFilterButton": False} if is_numeric_col(df, i) else {"filterPlaceholder": "Search..."},
        "minWidth": 120,
        "resizable": True,
        "sortable": True,
        "suppressMenu": True,
        "tooltipField": i, # Set the tooltip field to the column name
        "type": "numericColumn" if is_numeric_col(df, i) else "textColumn",
        "valueFormatter": {"function": "d3.format(',.0f')(params.value)"} if is_numeric_col(df, i) else None,
        "valueGetter": get_value_getter(i),
      }
      # Only add tooltipComponent for string columns
      if not is_numeric_col(df, i):
        column_def["tooltipComponent"] = "CustomTooltip"
      
      column_defs.append(column_def)
        
  return column_defs

# A callback to generate the grid
@app.callback(
  Output('grid-container', 'children'),
  Output('grid', 'rowData'),
  Output('grid', 'columnDefs'),
  [
    Input('btn-ep1', 'n_clicks'),
    Input('btn-ep2', 'n_clicks'),
    Input('btn-ep3', 'n_clicks')
  ]
)
def update_grid(n1, n2, n3):
  ctx = dash.callback_context
  if not ctx.triggered:
    data = df  # default data
  else:
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id == 'btn-ep1':
      data = df
    #elif button_id == 'btn-ep2':
      #data = ep2_df
    #elif button_id == 'btn-ep3':
      #data = ep3_df

  grid = dag.AgGrid(
    id='grid',
    rowData=data.to_dict('records'),
    columnDefs=generate_column_defs(data),
    dashGridOptions={"tooltipShowDelay": 300},
    #defaultColDef={"editable": False,  "tooltipComponent": "CustomTooltip"},
    className="ag-theme-alpine-dark",
    style={'height': '100%'}
    # ...other grid parameters...
  )
  return grid, data.to_dict('records'), generate_column_defs(data)

# Create a callback to update the column size to autoSize
# Gets triggered when the columnDefs property of the grid changes. This callback will then set the columnSize property to "autoSize"
@app.callback(
  Output('grid', 'columnSize'),
  [Input('grid', 'columnDefs')]
)
def update_column_size(_):
  return "responsiveSizeToFit"

# Create a callback to open a modal when a row is selected in the grid
# Based on https://dashaggrid.pythonanywhere.com/other-examples/popup-from-cell-click
@app.callback(
  Output("modal", "is_open"),
  Output("clicked-cell-unique-value", "data"),
  [
    Input("grid", "cellClicked"),
    Input("close", "n_clicks"),
  ],
  [State("modal", "is_open"), State("grid", "rowData")]
)
def open_modal(cell_clicked_data, close_btn_clicks, modal_open, grid_data):
  ctx = dash.callback_context
  if not ctx.triggered:
    return dash.no_update, dash.no_update

  button_id = ctx.triggered[0]['prop_id'].split('.')[0]

  if button_id == 'close':
    return False, dash.no_update

  elif button_id == 'grid':
    if not cell_clicked_data or 'rowIndex' not in cell_clicked_data:
      raise PreventUpdate

    # Extract the name of the clicked enemy using uuid
    row_id = cell_clicked_data['rowId']
    clicked_uuid = grid_data[int(row_id)]['uuid']
    return True, {"uuid": clicked_uuid}

  else:
    raise PreventUpdate

# Create a callback to populate the modal with the correct data
@app.callback(
  Output("modal-content", "children"),
  [Input("clicked-cell-unique-value", "data")],
  [State("btn-ep1", "n_clicks"), State("btn-ep2", "n_clicks"), State("btn-ep3", "n_clicks")]
)
def populate_modal(data, n1, n2, n3):
  if not data:
    raise PreventUpdate

  # Determine the correct dataframe based on the clicked episode button
  clicks = {
    'btn-ep1': n1 or 0,  # Default to 0 if None
    'btn-ep2': n2 or 0,
    'btn-ep3': n3 or 0
  }
  latest_button = max(clicks, key=clicks.get)

  if latest_button == 'btn-ep1':
    df = df
  #elif latest_button == 'btn-ep2':
    #df = ep2_df
  #elif latest_button == 'btn-ep3':
    #df = ep3_df

  # Check if the desired uuid exists in the dataset
  selected_rows = df[df["uuid"] == data["uuid"]]
  if selected_rows.empty:
    logger.error(f"UUID {data['uuid']} not found in dataset.")
    raise PreventUpdate

  selected_row = selected_rows.iloc[0]
  logger.debug(f"Selected Row Data: {selected_row}")  # Log the complete row data

  # Exclude the UUID from the displayed data
  selected_row = selected_row.drop("uuid")

  content = []
  for key, value in selected_row.items():
    if pd.api.types.is_numeric_dtype(value) and pd.notna(value):  # Check if value is numeric and not NaN
      formatted_value = f"{int(value):,}"  # Format as integer with thousands separator
    else:
      formatted_value = "N/A" if pd.isna(value) else value  # Replace NaN with "N/A", otherwise use value as-is
        
    logger.debug(f"Key: {key}, Formatted Value: {formatted_value}")  # Log each key-value pair
    content.append(f"**{key}:** {formatted_value}  \n")  # Use two spaces and a newline character for separate lines

  generated_content = ''.join(content)
  logger.debug(f"Generated Content: {generated_content}")  # Log the generated content
  return dcc.Markdown(generated_content)

# Create a callback to update the active state of the episode buttons
@app.callback(
  Output('btn-ep1', 'active'),
  Output('btn-ep2', 'active'),
  Output('btn-ep3', 'active'),
  Input('btn-ep1', 'n_clicks'),
  Input('btn-ep2', 'n_clicks'),
  Input('btn-ep3', 'n_clicks')
)
def update_button_active_state(n1, n2, n3):
  ctx = dash.callback_context
  if not ctx.triggered:
    return True, False, False  # Set "Episode I" button as active by default
  button_id = ctx.triggered[0]['prop_id'].split('.')[0]
  if button_id == 'btn-ep1':
    return True, False, False
  elif button_id == 'btn-ep2':
    return False, True, False
  elif button_id == 'btn-ep3':
    return False, False, True
  else:
    return True, False, False  # Default case


# Run the app if running locally
if __name__ == '__main__':
  app.run_server(debug=True)