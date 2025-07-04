package com.example;

public class Car extends Vehicle implements Drivable {
    private String model;
    private int year;

    public Car(String brand, String model, int year) {
        super(brand);
        this.model = model;
        this.year = year;
    }

    public String getModel() {
        return model;
    }

    public void setModel(String model) {
        this.model = model;
    }

    public int getYear() {
        return year;
    }

    public void setYear(int year) {
        this.year = year;
    }

    @Override
    public void start() {
        System.out.println(getBrand() + " " + getModel() + " starts the engine.");
    }

    @Override
    public void stop() {
        System.out.println(getBrand() + " " + getModel() + " stops the engine.");
    }

    @Override
    public void drive() {
        System.out.println(getBrand() + " " + getModel() + " is driving.");
    }
}

