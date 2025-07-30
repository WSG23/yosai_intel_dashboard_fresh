from api.adapter import create_api_app

from config.constants import API_PORT

app = create_api_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=API_PORT)
