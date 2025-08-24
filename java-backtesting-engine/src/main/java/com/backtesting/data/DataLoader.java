package com.backtesting.data;

import com.backtesting.models.TradingDayData;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.stream.Collectors;

/**
 * Unified data loading and parsing for option chains and spot prices
 */
public class DataLoader {
    private final String dataPath;

    public DataLoader(String dataPath) {
        this.dataPath = dataPath != null ? dataPath : "5SecData";
    }

    public DataLoader() {
        this("5SecData");
    }

    /**
     * Get list of available trading dates for a symbol
     */
    public List<String> getAvailableDates(String symbol) {
        Path symbolPath = Paths.get(dataPath, symbol.toUpperCase());
        System.out.println("Looking for data in: " + symbolPath.toAbsolutePath());
        
        if (!Files.exists(symbolPath)) {
            System.err.println("Directory does not exist: " + symbolPath.toAbsolutePath());
            return new ArrayList<>();
        }

        List<String> dates = new ArrayList<>();
        try {
            Files.list(symbolPath)
                .filter(path -> path.getFileName().toString().endsWith("_BK.csv"))
                .forEach(path -> {
                    String fileName = path.getFileName().toString();
                    String date = fileName.replace("_BK.csv", "");
                    dates.add(date);
                    System.out.println("Found data file: " + fileName + " -> date: " + date);
                });
        } catch (IOException e) {
            System.err.println("Error reading directory: " + symbolPath + " - " + e.getMessage());
        }

        List<String> sortedDates = dates.stream().sorted().collect(Collectors.toList());
        System.out.println("Available dates: " + sortedDates);
        return sortedDates;
    }

    /**
     * Load all data for a specific trading day
     */
    public TradingDayData loadTradingDay(String symbol, String date) {
        Path symbolPath = Paths.get(dataPath, symbol.toUpperCase());

        // Load option data
        Path optionFile = symbolPath.resolve(date + "_BK.csv");
        if (!Files.exists(optionFile)) {
            System.err.println("Option data file not found: " + optionFile);
            return null;
        }

        Map<Integer, Map<String, Map<Double, Double>>> optionData = parseOptionData(optionFile);

        // Load spot data
        Path spotFile = symbolPath.resolve("Spot").resolve(symbol.toLowerCase() + ".csv");
        Map<Integer, Double> spotData = parseSpotData(spotFile, date);

        // Load metadata
        Path propFile = symbolPath.resolve(date + ".prop");
        Map<String, Object> metadata = parsePropFile(propFile);

        int jobEndIdx = metadata.containsKey("jobEndIdx") ? 
                       (Integer) metadata.get("jobEndIdx") : 4660;

        return new TradingDayData(date, spotData, optionData, jobEndIdx, metadata);
    }

    /**
     * Parse option data CSV file
     */
    private Map<Integer, Map<String, Map<Double, Double>>> parseOptionData(Path filePath) {
        Map<Integer, Map<String, Map<Double, Double>>> optionData = new HashMap<>();

        try (BufferedReader reader = Files.newBufferedReader(filePath)) {
            String line;
            while ((line = reader.readLine()) != null) {
                String[] parts = line.split(",");
                if (parts.length >= 4) {
                    try {
                        int timestamp = Integer.parseInt(parts[0].trim());
                        String optionType = parts[1].trim(); // CE or PE
                        double strike = Double.parseDouble(parts[2].trim());
                        double price = Double.parseDouble(parts[3].trim());

                        optionData.computeIfAbsent(timestamp, k -> new HashMap<>())
                                 .computeIfAbsent(optionType, k -> new HashMap<>())
                                 .put(strike, price);
                    } catch (NumberFormatException e) {
                        // Skip invalid lines
                    }
                }
            }
        } catch (IOException e) {
            System.err.println("Error parsing option data " + filePath + ": " + e.getMessage());
        }

        return optionData;
    }

    /**
     * Parse spot price data CSV file for specific date
     */
    private Map<Integer, Double> parseSpotData(Path filePath, String targetDate) {
        Map<Integer, Double> spotData = new HashMap<>();

        try (BufferedReader reader = Files.newBufferedReader(filePath)) {
            String line;
            while ((line = reader.readLine()) != null) {
                String[] parts = line.split(",");
                if (parts.length >= 6 && parts[0].trim().equals(targetDate)) {
                    try {
                        int timestamp = Integer.parseInt(parts[1].trim());
                        double closePrice = Double.parseDouble(parts[5].trim()); // Using close price (6th column, index 5)
                        spotData.put(timestamp, closePrice);
                    } catch (NumberFormatException e) {
                        // Skip invalid lines
                    }
                }
            }
        } catch (IOException e) {
            System.err.println("Error parsing spot data " + filePath + ": " + e.getMessage());
        }

        return spotData;
    }

    /**
     * Parse .prop file for metadata
     */
    private Map<String, Object> parsePropFile(Path filePath) {
        Map<String, Object> metadata = new HashMap<>();

        try (BufferedReader reader = Files.newBufferedReader(filePath)) {
            String line;
            while ((line = reader.readLine()) != null) {
                line = line.trim();
                if (!line.isEmpty() && !line.startsWith("#") && line.contains("=")) {
                    String[] parts = line.split("=", 2);
                    String key = parts[0].trim();
                    String value = parts[1].trim();
                    
                    // Try to convert to integer if possible
                    try {
                        metadata.put(key, Integer.parseInt(value));
                    } catch (NumberFormatException e) {
                        metadata.put(key, value);
                    }
                }
            }
        } catch (IOException e) {
            System.err.println("Error parsing prop file " + filePath + ": " + e.getMessage());
        }

        return metadata;
    }

    /**
     * Get strikes closest to spot price
     */
    public List<Double> getStrikesNearSpot(double spotPrice, 
                                          Map<String, Map<Double, Double>> optionChain,
                                          int numStrikes) {
        Set<Double> allStrikes = new HashSet<>();
        
        for (Map<Double, Double> strikes : optionChain.values()) {
            allStrikes.addAll(strikes.keySet());
        }

        if (allStrikes.isEmpty()) {
            return new ArrayList<>();
        }

        // Sort strikes by distance from spot price
        return allStrikes.stream()
                .sorted((s1, s2) -> Double.compare(Math.abs(s1 - spotPrice), Math.abs(s2 - spotPrice)))
                .limit(numStrikes)
                .collect(Collectors.toList());
    }

    /**
     * Get option price for specific timestamp, type, and strike
     */
    public Double getOptionPrice(Map<Integer, Map<String, Map<Double, Double>>> optionData,
                                int timestamp, String optionType, double strike) {
        if (optionData.containsKey(timestamp) &&
            optionData.get(timestamp).containsKey(optionType) &&
            optionData.get(timestamp).get(optionType).containsKey(strike)) {
            return optionData.get(timestamp).get(optionType).get(strike);
        }
        return null;
    }
}