package com.example;

import java.util.Scanner;

public class MainApplication {

    public static void main(String[] args) {
        // Phase 2 & 3: OOP Concepts, Inheritance, Polymorphism
        System.out.println("\n--- Demonstrating OOP Concepts ---");
        Person person1 = new Person("Alice", 30);
        System.out.println("Initial Person: " + person1.getName() + ", " + person1.getAge());
        person1.setAge(31);
        System.out.println("Updated Person: " + person1.getName() + ", " + person1.getAge());

        Car myCar = new Car("Toyota", "Camry", 2020);
        myCar.start();
        myCar.drive();
        myCar.stop();

        Motorcycle myMotorcycle = new Motorcycle("Honda");
        myMotorcycle.start();
        myMotorcycle.stop();

        PolymorphismDemo polyDemo = new PolymorphismDemo();
        System.out.println("Static Polymorphism (add int): " + polyDemo.add(5, 10));
        System.out.println("Static Polymorphism (add int, int, int): " + polyDemo.add(1, 2, 3));
        System.out.println("Static Polymorphism (add double): " + polyDemo.add(5.5, 10.5));
        polyDemo.demonstrateDynamicPolymorphism();

        // Phase 4 & 5: Database Integration, MVC Pattern
        System.out.println("\n--- Demonstrating Database Integration and MVC ---");
        DatabaseManager dbManager = new DatabaseManager();
        ConsoleView consoleView = new ConsoleView();
        PersonController personController = new PersonController(dbManager, consoleView);

        // CRUD Operations
        personController.addPerson("Bob", 25);
        personController.addPerson("Charlie", 35);
        personController.viewAllPersons();

        personController.updatePersonAge("Bob", 26);
        personController.viewAllPersons();

        personController.deletePerson("Charlie");
        personController.viewAllPersons();

        // Error Handling (demonstrative - actual error handling is in DatabaseManager)
        System.out.println("\n--- Demonstrating Error Handling (conceptual) ---");
        try {
            // Simulate an operation that might fail
            int result = 10 / 0; // This will cause an ArithmeticException
        } catch (ArithmeticException e) {
            consoleView.displayError("Division by zero attempted!");
        } finally {
            consoleView.displayMessage("Error handling demonstration complete.");
        }

        // Demonstrating proper naming conventions and DRY principle
        // (already applied throughout the code, e.g., clear method names, reusable components)

        System.out.println("\n--- Application Demonstration Complete ---");
    }
}

