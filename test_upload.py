from dash import dcc, html

test_upload = dcc.Upload(
    id="test-upload",
    children=html.Div([
        "Drag and Drop or Click to Upload"
    ]),
    style={
        'width': '100%',
        'height': '200px',
        'lineHeight': '200px',
        'borderWidth': '2px',
        'borderStyle': 'dashed',
        'borderRadius': '5px',
        'textAlign': 'center',
        'margin': '10px',
        'backgroundColor': '#fafafa'
    },
    multiple=True
)

print("✅ Basic upload created")
print(str(test_upload))
