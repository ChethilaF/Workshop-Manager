from app import create_app

# Create the Flask application
app = create_app()

# Run the application with debug mode enabled
if __name__ == '__main__':
    app.run(debug=True)
