from api.adapter import create_api_app

app = create_api_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
