package com.example;

public class PolymorphismDemo {

    // Static Polymorphism (Method Overloading)
    public int add(int a, int b) {
        return a + b;
    }

    public int add(int a, int b, int c) {
        return a + b + c;
    }

    public double add(double a, double b) {
        return a + b;
    }

    // Dynamic Polymorphism (Method Overriding)
    public void demonstrateDynamicPolymorphism() {
        Vehicle car = new Car("Toyota", "Camry", 2020);
        Vehicle motorcycle = new Motorcycle("Honda");

        car.start();
        car.stop();

        motorcycle.start();
        motorcycle.stop();

        Drivable myCar = new Car("Ford", "Focus", 2018);
        myCar.drive();
    }
}

