package it.uniroma3;

import java.io.FileInputStream;
import java.io.IOException;
import java.util.Properties;

public class ConfigLoader {
    private static final String CONFIG_FILE = "src\\main\\resources\\config.properties";

    public static Properties loadConfig() {
        Properties props = new Properties();
        try (FileInputStream fis = new FileInputStream(CONFIG_FILE)) {
            props.load(fis);
        } catch (IOException e) {
            System.err.println("Error loading config.properties: " + e.getMessage());
        }
        return props;
    }
}
