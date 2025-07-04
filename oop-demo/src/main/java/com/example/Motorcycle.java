
package com.example;

public class Motorcycle extends Vehicle {
    public Motorcycle(String brand) {
        super(brand);
    }

    @Override
    public void start() {
        System.out.println(getBrand() + " motorcycle starts with a kick.");
    }

    @Override
    public void stop() {
        System.out.println(getBrand() + " motorcycle stops.");
    }
}

