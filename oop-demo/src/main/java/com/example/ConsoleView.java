package com.example;

import java.util.List;

public class ConsoleView {

    public void displayPerson(Person person) {
        System.out.println("Person: Name = " + person.getName() + ", Age = " + person.getAge());
    }

    public void displayAllPersons(List<Person> persons) {
        System.out.println("\n--- All Persons ---");
        if (persons.isEmpty()) {
            System.out.println("No persons in the database.");
        } else {
            for (Person person : persons) {
                displayPerson(person);
            }
        }
        System.out.println("-------------------");
    }

    public void displayMessage(String message) {
        System.out.println(message);
    }

    public void displayError(String error) {
        System.err.println("Error: " + error);
    }
}

