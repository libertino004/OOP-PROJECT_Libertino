
package com.example;

import java.util.List;

public class PersonController {
    private DatabaseManager model;
    private ConsoleView view;

    public PersonController(DatabaseManager model, ConsoleView view) {
        this.model = model;
        this.view = view;
    }

    public void addPerson(String name, int age) {
        Person person = new Person(name, age);
        model.addPerson(person);
        view.displayMessage("Person added: " + name);
    }

    public void viewAllPersons() {
        List<Person> persons = model.getAllPersons();
        view.displayAllPersons(persons);
    }

    public void updatePersonAge(String name, int newAge) {
        model.updatePersonAge(name, newAge);
        view.displayMessage("Person " + name + " age updated to " + newAge);
    }

    public void deletePerson(String name) {
        model.deletePerson(name);
        view.displayMessage("Person deleted: " + name);
    }
}

