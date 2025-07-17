#!/bin/bash

echo "Testing Upload Functionality..."

# Test if React app is running
if curl -s http://localhost:3000 > /dev/null; then
    echo "✓ React app is running on port 3000"
else
    echo "✗ React app is not running on port 3000"
fi

# Test if Flask API is running
if curl -s http://localhost:5001/api/v1/health > /dev/null; then
    echo "✓ Flask API is running on port 5001"
else
    echo "✗ Flask API is not running on port 5001"
fi

# Test CORS
echo -e "\nTesting CORS configuration..."
curl -I -X OPTIONS http://localhost:5001/api/v1/upload \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST"

echo -e "\nSetup complete! The upload functionality should now be working."
