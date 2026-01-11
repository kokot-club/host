from dotenv import load_dotenv
load_dotenv()

from web.app import create_app
app = create_app()

# debug mode
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8484, debug=True)