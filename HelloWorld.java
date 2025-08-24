public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello from Java 17!");
        System.out.println("Current working directory: " + System.getProperty("user.dir"));
        System.out.println("Java version: " + System.getProperty("java.version"));
        
        // Demonstrate some Java 17 features
        var message = "Java 17 features work!";
        System.out.println(message);
        
        // Text blocks (Java 13+)
        String multiline = """
            This is a text block
            spanning multiple lines
            in Java 17
            """;
        System.out.println(multiline);
    }
}