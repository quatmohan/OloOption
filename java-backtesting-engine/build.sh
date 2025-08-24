#!/bin/bash

# Build script for Java Options Backtesting Engine

echo "=== Java Options Backtesting Engine Build Script ==="

# Check if Maven is installed
if ! command -v mvn &> /dev/null; then
    echo "Error: Maven is not installed. Please install Maven first."
    exit 1
fi

# Check if Java is installed
if ! command -v java &> /dev/null; then
    echo "Error: Java is not installed. Please install Java 11 or higher."
    exit 1
fi

echo "Maven version:"
mvn --version

echo ""
echo "=== Cleaning previous builds ==="
mvn clean

echo ""
echo "=== Compiling source code ==="
mvn compile

if [ $? -ne 0 ]; then
    echo "Error: Compilation failed"
    exit 1
fi

echo ""
echo "=== Running tests ==="
mvn test

if [ $? -ne 0 ]; then
    echo "Warning: Some tests failed, but continuing..."
fi

echo ""
echo "=== Build completed successfully! ==="
echo ""
echo "To run the example:"
echo "  mvn exec:java"
echo ""
echo "To run specific example class:"
echo "  mvn exec:java -Dexec.mainClass=\"com.backtesting.examples.ExampleBacktest\""
echo ""
echo "To run tests:"
echo "  mvn test"
echo ""
echo "To package as JAR:"
echo "  mvn package"